# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class DbRelatedManager(models.Manager):
    def get_queryset(self):
        return super(DbRelatedManager, self).get_queryset().using('moodle')

class MdlCohort(models.Model):
    id = models.BigAutoField(primary_key=True)
    contextid = models.BigIntegerField()
    name = models.CharField(max_length=254)
    idnumber = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    descriptionformat = models.IntegerField()
    visible = models.IntegerField()
    component = models.CharField(max_length=100)
    timecreated = models.BigIntegerField()
    timemodified = models.BigIntegerField()
    theme = models.CharField(max_length=50, blank=True, null=True)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_cohort'


class MdlCohortMembers(models.Model):
    id = models.BigAutoField(primary_key=True)
    cohortid = models.ForeignKey(MdlCohort, on_delete=models.CASCADE, db_column='cohortid')
    userid = models.ForeignKey('MdlUser', on_delete=models.CASCADE, db_column='userid')
    timeadded = models.BigIntegerField()

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_cohort_members'
        unique_together = (('cohortid', 'userid'),)


class MdlCourse(models.Model):
    id = models.BigAutoField(primary_key=True)
    category = models.BigIntegerField()
    sortorder = models.BigIntegerField()
    fullname = models.CharField(max_length=254)
    shortname = models.CharField(max_length=255)
    idnumber = models.CharField(max_length=100)
    summary = models.TextField(blank=True, null=True)
    summaryformat = models.IntegerField()
    format = models.CharField(max_length=21)
    showgrades = models.IntegerField()
    newsitems = models.IntegerField()
    startdate = models.BigIntegerField()
    enddate = models.BigIntegerField()
    relativedatesmode = models.IntegerField()
    marker = models.BigIntegerField()
    maxbytes = models.BigIntegerField()
    legacyfiles = models.SmallIntegerField()
    showreports = models.SmallIntegerField()
    visible = models.IntegerField()
    visibleold = models.IntegerField()
    downloadcontent = models.IntegerField(blank=True, null=True)
    groupmode = models.SmallIntegerField()
    groupmodeforce = models.SmallIntegerField()
    defaultgroupingid = models.BigIntegerField()
    lang = models.CharField(max_length=30)
    calendartype = models.CharField(max_length=30)
    theme = models.CharField(max_length=50)
    timecreated = models.BigIntegerField()
    timemodified = models.BigIntegerField()
    requested = models.IntegerField()
    enablecompletion = models.IntegerField()
    completionnotify = models.IntegerField()
    cacherev = models.BigIntegerField()
    originalcourseid = models.BigIntegerField(blank=True, null=True)
    showactivitydates = models.IntegerField()
    showcompletionconditions = models.IntegerField(blank=True, null=True)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_course'


class MdlUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    auth = models.CharField(max_length=20)
    confirmed = models.IntegerField()
    policyagreed = models.IntegerField()
    deleted = models.IntegerField()
    suspended = models.IntegerField()
    mnethostid = models.BigIntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)
    idnumber = models.CharField(max_length=255)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    emailstop = models.IntegerField()
    phone1 = models.CharField(max_length=20)
    phone2 = models.CharField(max_length=20)
    institution = models.CharField(max_length=255)
    department = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    country = models.CharField(max_length=2)
    lang = models.CharField(max_length=30)
    calendartype = models.CharField(max_length=30)
    theme = models.CharField(max_length=50)
    timezone = models.CharField(max_length=100)
    firstaccess = models.BigIntegerField()
    lastaccess = models.BigIntegerField()
    lastlogin = models.BigIntegerField()
    currentlogin = models.BigIntegerField()
    lastip = models.CharField(max_length=45)
    secret = models.CharField(max_length=15)
    picture = models.BigIntegerField()
    description = models.TextField(blank=True, null=True)
    descriptionformat = models.IntegerField()
    mailformat = models.IntegerField()
    maildigest = models.IntegerField()
    maildisplay = models.IntegerField()
    autosubscribe = models.IntegerField()
    trackforums = models.IntegerField()
    timecreated = models.BigIntegerField()
    timemodified = models.BigIntegerField()
    trustbitmask = models.BigIntegerField()
    imagealt = models.CharField(max_length=255, blank=True, null=True)
    lastnamephonetic = models.CharField(max_length=255, blank=True, null=True)
    firstnamephonetic = models.CharField(max_length=255, blank=True, null=True)
    middlename = models.CharField(max_length=255, blank=True, null=True)
    alternatename = models.CharField(max_length=255, blank=True, null=True)
    moodlenetprofile = models.CharField(max_length=255, db_collation='utf8mb4_unicode_ci', blank=True, null=True)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_user'
        unique_together = (('mnethostid', 'username'),)


class MdlUserEnrolments(models.Model):
    id = models.BigAutoField(primary_key=True)
    status = models.BigIntegerField()
    enrolid = models.ForeignKey('MdlEnrol', on_delete=models.CASCADE, db_column='enrolid')
    userid = models.ForeignKey('MdlUser', on_delete=models.CASCADE, db_column='userid')
    timestart = models.BigIntegerField()
    timeend = models.BigIntegerField()
    modifierid = models.BigIntegerField()
    timecreated = models.BigIntegerField()
    timemodified = models.BigIntegerField()

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_user_enrolments'
        unique_together = (('enrolid', 'userid'),)


class MdlEnrol(models.Model):
    id = models.BigAutoField(primary_key=True)
    enrol = models.CharField(max_length=20)
    status = models.BigIntegerField()
    courseid = models.ForeignKey(MdlCourse, on_delete=models.CASCADE, db_column='courseid')
    sortorder = models.BigIntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)
    enrolperiod = models.BigIntegerField(blank=True, null=True)
    enrolstartdate = models.BigIntegerField(blank=True, null=True)
    enrolenddate = models.BigIntegerField(blank=True, null=True)
    expirynotify = models.IntegerField(blank=True, null=True)
    expirythreshold = models.BigIntegerField(blank=True, null=True)
    notifyall = models.IntegerField(blank=True, null=True)
    password = models.CharField(max_length=50, blank=True, null=True)
    cost = models.CharField(max_length=20, blank=True, null=True)
    currency = models.CharField(max_length=3, blank=True, null=True)
    roleid = models.BigIntegerField(blank=True, null=True)
    customint1 = models.BigIntegerField(blank=True, null=True)
    customint2 = models.BigIntegerField(blank=True, null=True)
    customint3 = models.BigIntegerField(blank=True, null=True)
    customint4 = models.BigIntegerField(blank=True, null=True)
    customint5 = models.BigIntegerField(blank=True, null=True)
    customint6 = models.BigIntegerField(blank=True, null=True)
    customint7 = models.BigIntegerField(blank=True, null=True)
    customint8 = models.BigIntegerField(blank=True, null=True)
    customchar1 = models.CharField(max_length=255, blank=True, null=True)
    customchar2 = models.CharField(max_length=255, blank=True, null=True)
    customchar3 = models.CharField(max_length=1333, blank=True, null=True)
    customdec1 = models.DecimalField(max_digits=12, decimal_places=7, blank=True, null=True)
    customdec2 = models.DecimalField(max_digits=12, decimal_places=7, blank=True, null=True)
    customtext1 = models.TextField(blank=True, null=True)
    customtext2 = models.TextField(blank=True, null=True)
    customtext3 = models.TextField(blank=True, null=True)
    customtext4 = models.TextField(blank=True, null=True)
    timecreated = models.BigIntegerField()
    timemodified = models.BigIntegerField()

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_enrol'

class MdlRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255)
    shortname = models.CharField(unique=True, max_length=100)
    description = models.TextField()
    sortorder = models.BigIntegerField(unique=True)
    archetype = models.CharField(max_length=30)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_role'

class MdlRoleAssignments(models.Model):
    id = models.BigAutoField(primary_key=True)
    roleid = models.ForeignKey(MdlRole, on_delete=models.CASCADE, db_column='roleid')
    contextid = models.BigIntegerField()
    userid = models.ForeignKey(MdlUser, on_delete=models.CASCADE, db_column='userid')
    timemodified = models.BigIntegerField()
    modifierid = models.BigIntegerField()
    component = models.CharField(max_length=100)
    itemid = models.BigIntegerField()
    sortorder = models.BigIntegerField()

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_role_assignments'
