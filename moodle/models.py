from django.db import models

class DbRelatedManager(models.Manager):
    def get_queryset(self):
        return super(DbRelatedManager, self).get_queryset().using('moodle')

class MdlCohort(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=254)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_cohort'

class MdlCohortMembers(models.Model):
    id = models.BigAutoField(primary_key=True)
    cohortid = models.ForeignKey(MdlCohort, on_delete=models.CASCADE, db_column='cohortid')
    userid = models.ForeignKey('MdlUser', on_delete=models.CASCADE, db_column='userid')

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_cohort_members'
        unique_together = (('cohortid', 'userid'),)

class MdlCourse(models.Model):
    id = models.BigAutoField(primary_key=True)
    fullname = models.CharField(max_length=254)
    shortname = models.CharField(max_length=255)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_course'

class MdlUser(models.Model):
    id = models.BigAutoField(primary_key=True)
    mnethostid = models.BigIntegerField()
    username = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.CharField(max_length=100)

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

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_user_enrolments'
        unique_together = (('enrolid', 'userid'),)

class MdlEnrol(models.Model):
    id = models.BigAutoField(primary_key=True)
    enrol = models.CharField(max_length=20)
    courseid = models.ForeignKey(MdlCourse, on_delete=models.CASCADE, db_column='courseid')

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_enrol'

class MdlRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    shortname = models.CharField(unique=True, max_length=100)

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_role'

class MdlRoleAssignments(models.Model):
    id = models.BigAutoField(primary_key=True)
    roleid = models.ForeignKey(MdlRole, on_delete=models.CASCADE, db_column='roleid')
    userid = models.ForeignKey(MdlUser, on_delete=models.CASCADE, db_column='userid')

    objects = DbRelatedManager()

    class Meta:
        managed = False
        db_table = 'mdl_role_assignments'
