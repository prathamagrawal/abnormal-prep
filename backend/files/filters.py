from django.db.models import QuerySet
from django.utils.dateparse import parse_datetime

from files.log_config import get_logger
from files.models import File

logger = get_logger("filters")


class FileQueryFilter:
    @classmethod
    def apply(cls, queryset: QuerySet, query_params) -> QuerySet:
        params = query_params

        search = params.get("search")
        if search:
            search = str(search)[:200]
            queryset = queryset.filter(original_filename__icontains=search)

        file_type = params.get("file_type")
        if file_type:
            queryset = queryset.filter(file_type=file_type)

        min_size = params.get("min_size")
        if min_size is not None and min_size != "":
            parsed_min = cls._parse_positive_int(min_size)
            if parsed_min is not None:
                queryset = queryset.filter(size__gte=parsed_min)

        max_size = params.get("max_size")
        if max_size is not None and max_size != "":
            parsed_max = cls._parse_positive_int(max_size)
            if parsed_max is not None:
                queryset = queryset.filter(size__lte=parsed_max)

        start_date = params.get("start_date")
        if start_date:
            parsed = parse_datetime(start_date)
            if parsed is not None:
                queryset = queryset.filter(uploaded_at__gte=parsed)

        end_date = params.get("end_date")
        if end_date:
            parsed = parse_datetime(end_date)
            if parsed is not None:
                queryset = queryset.filter(uploaded_at__lte=parsed)

        return queryset

    @staticmethod
    def _parse_positive_int(value: str) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed >= 0 else None
