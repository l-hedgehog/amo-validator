from django.db import models

import amo.models
from constants.applications import APPS_CHOICES
from versions import compare


class ApplicationManager(amo.models.ManagerBase):

    def supported(self):
        """Exclude unsupported apps."""
        return self.exclude(supported=False)


class AppVersion(amo.models.ModelBase):

    application = models.PositiveIntegerField(choices=APPS_CHOICES,
                                              db_column='application_id')
    version = models.CharField(max_length=255, default='')
    version_int = models.BigIntegerField(editable=False)

    class Meta:
        db_table = 'appversions'
        ordering = ['-version_int']
        unique_together = ('application', 'version')

    def save(self, *args, **kw):
        if not self.version_int:
            self.version_int = compare.version_int(self.version)
        return super(AppVersion, self).save(*args, **kw)

    def __init__(self, *args, **kwargs):
        super(AppVersion, self).__init__(*args, **kwargs)
        # Add all the major, minor, ..., version attributes to the object.
        self.__dict__.update(compare.version_dict(self.version or ''))

    def __unicode__(self):
        return self.version

    def flush_urls(self):
        return ['*/pages/appversions/*']