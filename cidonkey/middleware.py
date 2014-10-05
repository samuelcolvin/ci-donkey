from django.db import connection
from django.utils.log import getLogger

logger = getLogger('django')

class QueryCountDebugMiddleware(object):
    """
    https://gist.github.com/j4mie/956843
    This middleware will log the number of queries run
    and the total time taken for each request (with a
    status code of 200). It does not currently support
    multi-db setups.
    """
    def process_response(self, request, response):
        if response.status_code == 200:
            total_time = 0

            for query in connection.queries:
                query_time = query.get('time')
                # print query
                # print ''
                if query_time is None:
                    # django-debug-toolbar
                    query_time = query.get('duration', 0) / 1000
                total_time += float(query_time)
            logger.warn('%s queries run, total %s seconds', len(connection.queries), total_time)
        return response
