from distutils.core import setup

setup(
    name='django-rest-form-fields',
    version='1.0.0',
    packages=['django_rest_form_fields'],
    package_dir={'': 'src'},
    url='https://github.com/M1hacka/django-rest-form-fields',
    license='BSD 3-clause "New" or "Revised" License',
    author='Mikhail Shvein',
    author_email='work_shvein_mihail@mail.ru',
    description='Extended form fields to validate REST-request data via django.forms'
)
