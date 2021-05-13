import re
from django.core.validators import URLValidator


class URLValidatorWithUnderscoreDomain(URLValidator):
    hostname_re = r'[a-z' + URLValidator.ul + r'0-9](?:[a-z' + URLValidator.ul + r'0-9-_]{0,61}[a-z' \
                  + URLValidator.ul + r'0-9])?'
    host_re = '(' + hostname_re + URLValidator.domain_re + URLValidator.tld_re + '|localhost)'

    regex = re.compile(
        r'^(?:[a-z0-9.+-]*)://'  # scheme is validated separately
        r'(?:[^\s:@/]+(?::[^\s:@/]*)?@)?'  # user:pass authentication
        r'(?:' + URLValidator.ipv4_re + '|' + URLValidator.ipv6_re + '|' + host_re + ')'
        r'(?::\d{2,5})?'  # port
        r'(?:[/?#][^\s]*)?'  # resource path
        r'\Z', re.IGNORECASE)
