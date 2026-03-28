from .models import SiteMetric


def site_metrics(_request):
    return {"site_total_visits": SiteMetric.cached_total_visits()}
