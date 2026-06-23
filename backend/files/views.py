from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from files.filters import FileQueryFilter
from files.log_config import get_logger
from files.models import File, UserStorageMetrics
from files.serializers import FileSerializer
from files.services import StorageQuotaExceeded, delete_file, upload_file

logger = get_logger("views")


class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    USER_ID_HEADER = "UserId"

    def _require_user_id(self) -> str | None:
        user_id = self.request.headers.get(self.USER_ID_HEADER)
        if not user_id:
            return None
        user_id = user_id.strip()
        return user_id or None

    def _bad_request_without_user(self):
        return Response(
            {"error": "UserId header is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def get_queryset(self):
        user_id = self._require_user_id()
        if not user_id:
            return File.objects.none()
        queryset = File.objects.filter(user_id=user_id)
        if self.action == "list":
            queryset = FileQueryFilter.apply(queryset, self.request.query_params)
        return queryset

    def list(self, request, *args, **kwargs):
        user_id = self._require_user_id()
        if not user_id:
            return self._bad_request_without_user()
        logger.info(
            "list_files user_id=%s filters=%s",
            user_id,
            dict(request.query_params),
        )
        response = super().list(request, *args, **kwargs)
        logger.info(
            "list_files_result user_id=%s count=%s",
            user_id,
            response.data.get("count", len(response.data)),
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        if not self._require_user_id():
            return self._bad_request_without_user()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        user_id = self._require_user_id()
        if not user_id:
            return self._bad_request_without_user()

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            "upload_request user_id=%s filename=%s size=%s type=%s",
            user_id,
            file_obj.name,
            file_obj.size,
            file_obj.content_type,
        )
        try:
            record = upload_file(
                user_id=user_id,
                uploaded_file=file_obj,
                original_filename=file_obj.name,
                file_type=file_obj.content_type or "application/octet-stream",
                size=file_obj.size,
            )
        except StorageQuotaExceeded:
            logger.warning("upload_rejected_quota user_id=%s", user_id)
            return Response(
                "Storage Quota Exceeded",
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(
            self.get_serializer(record).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        user_id = self._require_user_id()
        if not user_id:
            return self._bad_request_without_user()

        file_id = self.get_object().id
        logger.info("delete_request user_id=%s file_id=%s", user_id, file_id)
        delete_file(user_id=user_id, file_id=file_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], url_path="storage_stats")
    def storage_stats(self, request):
        user_id = self._require_user_id()
        if not user_id:
            return self._bad_request_without_user()
        stats = UserStorageMetrics.for_user(user_id).as_stats()
        logger.info("storage_stats user_id=%s stats=%s", user_id, stats)
        return Response(stats)

    @action(detail=False, methods=["get"], url_path="file_types")
    def file_types(self, request):
        user_id = self._require_user_id()
        if not user_id:
            return self._bad_request_without_user()
        types = (
            File.objects.filter(user_id=user_id)
            .values_list("file_type", flat=True)
            .distinct()
            .order_by("file_type")
        )
        type_list = list(types)
        logger.info("file_types user_id=%s count=%s", user_id, len(type_list))
        return Response(type_list)
