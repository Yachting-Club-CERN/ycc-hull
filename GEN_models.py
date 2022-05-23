# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Admin(models.Model):
    member_id = models.BigIntegerField(unique=True)
    rights = models.FloatField(blank=True, null=True)
    modified = models.DateField(blank=True, null=True)
    comments = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin'


class AdminValues(models.Model):
    right = models.CharField(max_length=20, blank=True, null=True)
    value = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'admin_values'


class AgendaEmpty(models.Model):
    day = models.DateField()
    start_time = models.DateField(blank=True, null=True)
    end_time = models.DateField(blank=True, null=True)
    submitter = models.FloatField()
    type = models.CharField(max_length=20)
    title = models.CharField(max_length=100)
    place = models.CharField(max_length=100, blank=True, null=True)
    text = models.CharField(max_length=500, blank=True, null=True)
    url = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'agenda_empty'


class Ba5Obsolete(models.Model):
    id = models.IntegerField()
    prefix = models.CharField(max_length=20, blank=True, null=True)
    name = models.CharField(max_length=6, blank=True, null=True)
    comments = models.CharField(max_length=22, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ba5_obsolete'


class Ba5AssignObsolete(models.Model):
    keyid = models.IntegerField(blank=True, null=True)
    member = models.ForeignKey('Members', models.DO_NOTHING, blank=True, null=True)
    assigned_date = models.DateField(blank=True, null=True)
    return_date = models.DateField(blank=True, null=True)
    comments = models.CharField(max_length=50, blank=True, null=True)
    last_verif = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ba5assign_obsolete'


class BoatKeys(models.Model):
    boat_id = models.IntegerField(primary_key=True)
    key_nr = models.IntegerField()
    locked = models.BooleanField(blank=True, null=True)
    virtual = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'boat_keys'


class Boats(models.Model):
    boat_id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=20)
    type = models.CharField(max_length=20)
    ycc_num = models.IntegerField(unique=True)
    license = models.CharField(max_length=5)
    class_field = models.CharField(db_column='class', max_length=5)  # Field renamed because it was a Python reserved word.
    table_pos = models.IntegerField(unique=True)
    maintainer_id = models.FloatField(blank=True, null=True)
    ext_reg_cat = models.CharField(max_length=2, blank=True, null=True)
    maintainer_id2 = models.ForeignKey('Members', models.DO_NOTHING, db_column='maintainer_id2', blank=True, null=True)
    registration_pdf = models.BinaryField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'boats'


class Buvette(models.Model):
    res_id = models.FloatField(primary_key=True)
    member_id = models.FloatField()
    day = models.DateField()
    quantity = models.IntegerField()
    modified = models.DateField()
    menu = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'buvette'


class ClassesObsolete2001(models.Model):
    class_id = models.FloatField()
    course_id = models.IntegerField()
    teacher = models.ForeignKey('Members', models.DO_NOTHING)
    helper = models.ForeignKey('Members', models.DO_NOTHING, blank=True, null=True)
    course_year = models.IntegerField()
    day_class = models.CharField(max_length=3, blank=True, null=True)
    lang = models.CharField(max_length=2, blank=True, null=True)
    notes = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'classes_obsolete2001'
        unique_together = (('class_id', 'teacher', 'course_year'),)


class Committee(models.Model):
    member = models.OneToOneField('Members', models.DO_NOTHING, primary_key=True)
    cyear = models.IntegerField()
    lcomments = models.CharField(max_length=100, blank=True, null=True)
    photo = models.CharField(max_length=50, blank=True, null=True)
    position = models.FloatField(blank=True, null=True)
    roles = models.CharField(max_length=500, blank=True, null=True)
    commid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'committee'
        unique_together = (('member', 'cyear'),)


class Countries(models.Model):
    country_name = models.CharField(max_length=50)
    country_code = models.CharField(primary_key=True, max_length=2)

    class Meta:
        managed = False
        db_table = 'countries'


class CoursesObs(models.Model):
    member = models.OneToOneField('Members', models.DO_NOTHING, primary_key=True)
    class_id = models.FloatField()
    pref_days = models.CharField(max_length=20, blank=True, null=True)
    pref_lang = models.CharField(max_length=10, blank=True, null=True)
    notes = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'courses_obs'
        unique_together = (('member', 'class_id'),)


class DeletedMemberApps(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)

    class Meta:
        managed = False
        db_table = 'deleted_member_apps'


class EmailQueueTable(models.Model):
    id = models.IntegerField(primary_key=True)
    from_field = models.CharField(max_length=100, blank=True, null=True)
    to_field = models.CharField(max_length=4000, blank=True, null=True)
    subject = models.CharField(max_length=200, blank=True, null=True)
    body = models.CharField(max_length=4000, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    time_stamp = models.DateTimeField(blank=True, null=True)
    cc_field = models.CharField(max_length=4000, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'email_queue_table'


class EmailTemplates(models.Model):
    id = models.IntegerField(blank=True, null=True)
    body = models.CharField(max_length=4000, blank=True, null=True)
    description = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'email_templates'


class EntranceFeesrecords(models.Model):
    member_id = models.FloatField(primary_key=True)
    year_f = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'entrance_feesrecords'
        unique_together = (('member_id', 'year_f'),)


class Fees(models.Model):
    cat_id = models.CharField(primary_key=True, max_length=2)
    description = models.CharField(max_length=25)
    entrance_fee = models.FloatField()
    annual_fee = models.FloatField()
    lastchange = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'fees'


class FeescoursesLastentry2005Obs(models.Model):
    member_id = models.FloatField()
    year_c = models.IntegerField()
    course = models.CharField(max_length=2)
    paid_date = models.DateField(blank=True, null=True)
    paid_mode = models.CharField(max_length=4, blank=True, null=True)
    feecourse = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'feescourses_lastentry2005_obs'


class Feesrecords(models.Model):
    member_id = models.FloatField()
    year_f = models.IntegerField()
    paid_date = models.DateField(blank=True, null=True)
    paid_mode = models.CharField(max_length=4, blank=True, null=True)
    fee = models.IntegerField()
    entered_date = models.DateField(blank=True, null=True)
    paymentid = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'feesrecords'


class Holidays(models.Model):
    day = models.DateField()
    label = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'holidays'


class ImportantDates(models.Model):
    id = models.FloatField(primary_key=True)
    datetime = models.DateField(blank=True, null=True)
    what = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = 'important_dates'


class ImportantValues(models.Model):
    id = models.IntegerField(primary_key=True)
    what = models.CharField(max_length=50)
    val = models.CharField(max_length=50)
    last_modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'important_values'


class Infolicences(models.Model):
    infoid = models.FloatField(primary_key=True)
    ncourse = models.CharField(max_length=2, blank=True, null=True)
    nlicence = models.CharField(max_length=2, blank=True, null=True)
    nkey = models.CharField(max_length=2, blank=True, null=True)
    description = models.CharField(max_length=50)
    coursefee = models.IntegerField(blank=True, null=True)
    course_name = models.CharField(max_length=30, blank=True, null=True)
    course_active = models.CharField(max_length=1, blank=True, null=True)
    course_level = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'infolicences'


class Keys(models.Model):
    member = models.ForeignKey('Members', models.DO_NOTHING)
    key_id = models.FloatField(primary_key=True)
    kyear = models.FloatField()

    class Meta:
        managed = False
        db_table = 'keys'
        unique_together = (('key_id', 'member', 'kyear'),)


class Keyslog(models.Model):
    keyslog_id = models.FloatField(primary_key=True)
    boat = models.ForeignKey(Boats, models.DO_NOTHING)
    taken_by = models.FloatField()
    returned_by = models.FloatField(blank=True, null=True)
    taken = models.DateField()
    returned = models.DateField(blank=True, null=True)
    log_id = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'keyslog'


class Licences(models.Model):
    member = models.ForeignKey('Members', models.DO_NOTHING)
    licence_id = models.IntegerField(primary_key=True)
    lyear = models.IntegerField()
    lcomments = models.CharField(max_length=100, blank=True, null=True)
    test_id = models.FloatField(blank=True, null=True)
    status = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'licences'
        unique_together = (('licence_id', 'member'),)


class Lottery(models.Model):
    id = models.FloatField(primary_key=True)
    year = models.IntegerField()
    member_id = models.FloatField()
    course1 = models.CharField(max_length=2, blank=True, null=True)
    course2 = models.CharField(max_length=2, blank=True, null=True)
    weekdays = models.CharField(max_length=21, blank=True, null=True)
    level0 = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lottery'
        unique_together = (('year', 'member_id'),)


class LotteryPlaces(models.Model):
    key = models.CharField(primary_key=True, max_length=2)
    places = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lottery_places'


class LotteryResults(models.Model):
    id = models.FloatField(primary_key=True)
    member_id = models.FloatField()
    year = models.IntegerField()
    drawn_seq = models.FloatField()
    withdrawn = models.CharField(max_length=1, blank=True, null=True)
    wd_comment = models.CharField(max_length=1000, blank=True, null=True)
    course_day = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lottery_results'
        unique_together = (('member_id', 'year'), ('drawn_seq', 'year'),)


class LotteryResultsArchive(models.Model):
    id = models.FloatField(blank=True, null=True)
    member_id = models.FloatField()
    year = models.IntegerField()
    drawn_seq = models.FloatField()
    withdrawn = models.CharField(max_length=1, blank=True, null=True)
    wd_comment = models.CharField(max_length=1000, blank=True, null=True)
    course_day = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'lottery_results_archive'


class Members(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)
    birthday = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=3, blank=True, null=True)
    membership = models.CharField(max_length=2)
    temp_memb = models.BooleanField(blank=True, null=True)
    lang1 = models.CharField(max_length=3, blank=True, null=True)
    lang2 = models.CharField(max_length=3, blank=True, null=True)
    category = models.CharField(max_length=1, blank=True, null=True)
    work_address1 = models.CharField(max_length=50, blank=True, null=True)
    work_address2 = models.CharField(max_length=50, blank=True, null=True)
    work_towncode = models.CharField(max_length=7, blank=True, null=True)
    work_town = models.CharField(max_length=25, blank=True, null=True)
    work_state = models.CharField(max_length=5, blank=True, null=True)
    work_phone = models.CharField(max_length=25, blank=True, null=True)
    e_mail = models.CharField(max_length=50, blank=True, null=True)
    home_addr = models.CharField(max_length=50)
    home_towncode = models.CharField(max_length=7, blank=True, null=True)
    home_town = models.CharField(max_length=25, blank=True, null=True)
    home_state = models.CharField(max_length=5, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mail_preference = models.CharField(max_length=1, blank=True, null=True)
    favourite_mailing_post = models.CharField(max_length=1, blank=True, null=True)
    member_entrance = models.CharField(max_length=4)
    cell_phone = models.CharField(max_length=25, blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    valid_until_date = models.DateField(blank=True, null=True)
    last_updated_date = models.DateField(blank=True, null=True)
    valid_from_date = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'members'


class MembersXxEmpty(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)
    birthday = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=3, blank=True, null=True)
    membership = models.CharField(max_length=2)
    pref_lang = models.CharField(max_length=1, blank=True, null=True)
    lang2 = models.CharField(max_length=1, blank=True, null=True)
    category = models.CharField(max_length=1, blank=True, null=True)
    resid = models.CharField(max_length=2, blank=True, null=True)
    address1 = models.CharField(max_length=50, blank=True, null=True)
    address2 = models.CharField(max_length=50, blank=True, null=True)
    towncode = models.CharField(max_length=7, blank=True, null=True)
    town = models.CharField(max_length=25, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    work_phone = models.CharField(max_length=20, blank=True, null=True)
    home_phone = models.CharField(max_length=20, blank=True, null=True)
    cell_phone = models.CharField(max_length=20, blank=True, null=True)
    e_mail = models.CharField(max_length=50, blank=True, null=True)
    mail_preference = models.CharField(max_length=1, blank=True, null=True)
    member_entrance = models.CharField(max_length=2)

    class Meta:
        managed = False
        db_table = 'members_xx_empty'


class Membership(models.Model):
    mb_id = models.IntegerField()
    mb_name = models.CharField(max_length=2)
    e_desc = models.CharField(max_length=20)
    f_desc = models.CharField(max_length=20)
    comments = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'membership'


class MembershipApplications(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)
    birthday = models.DateField()
    nationality = models.CharField(max_length=3, blank=True, null=True)
    membership = models.CharField(max_length=2)
    temp_memb = models.BooleanField(blank=True, null=True)
    lang1 = models.CharField(max_length=3, blank=True, null=True)
    lang2 = models.CharField(max_length=3, blank=True, null=True)
    category = models.CharField(max_length=1)
    work_address1 = models.CharField(max_length=50, blank=True, null=True)
    work_address2 = models.CharField(max_length=50, blank=True, null=True)
    work_towncode = models.CharField(max_length=7, blank=True, null=True)
    work_town = models.CharField(max_length=25, blank=True, null=True)
    work_state = models.CharField(max_length=5, blank=True, null=True)
    work_phone = models.CharField(max_length=25, blank=True, null=True)
    e_mail = models.CharField(max_length=50, blank=True, null=True)
    home_addr = models.CharField(max_length=50, blank=True, null=True)
    home_towncode = models.CharField(max_length=7, blank=True, null=True)
    home_town = models.CharField(max_length=25, blank=True, null=True)
    home_state = models.CharField(max_length=5, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mail_preference = models.CharField(max_length=1, blank=True, null=True)
    favourite_mailing_post = models.CharField(max_length=1, blank=True, null=True)
    member_entrance = models.CharField(max_length=4, blank=True, null=True)
    cell_phone = models.CharField(max_length=25, blank=True, null=True)
    logon_id = models.CharField(unique=True, max_length=25, blank=True, null=True)
    logon_passwd = models.CharField(max_length=25, blank=True, null=True)
    course1 = models.CharField(max_length=2, blank=True, null=True)
    course2 = models.CharField(max_length=2, blank=True, null=True)
    print_received = models.CharField(max_length=1, blank=True, null=True)
    submitted_date = models.DateField(blank=True, null=True)
    last_updated_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    logon_pass2 = models.CharField(max_length=128, blank=True, null=True)
    pass_reset_key = models.CharField(max_length=64, blank=True, null=True)
    pass_reset_exp = models.DateField(blank=True, null=True)
    last_changed = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'membership_applications'


class MembershipApplicationsToDel(models.Model):
    id = models.FloatField()
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)
    birthday = models.DateField()
    nationality = models.CharField(max_length=3, blank=True, null=True)
    membership = models.CharField(max_length=2)
    temp_memb = models.BooleanField(blank=True, null=True)
    lang1 = models.CharField(max_length=3, blank=True, null=True)
    lang2 = models.CharField(max_length=3, blank=True, null=True)
    category = models.CharField(max_length=1)
    work_address1 = models.CharField(max_length=50, blank=True, null=True)
    work_address2 = models.CharField(max_length=50, blank=True, null=True)
    work_towncode = models.CharField(max_length=7, blank=True, null=True)
    work_town = models.CharField(max_length=25, blank=True, null=True)
    work_state = models.CharField(max_length=5, blank=True, null=True)
    work_phone = models.CharField(max_length=25, blank=True, null=True)
    e_mail = models.CharField(max_length=50, blank=True, null=True)
    home_addr = models.CharField(max_length=50, blank=True, null=True)
    home_towncode = models.CharField(max_length=7, blank=True, null=True)
    home_town = models.CharField(max_length=25, blank=True, null=True)
    home_state = models.CharField(max_length=5, blank=True, null=True)
    home_phone = models.CharField(max_length=25, blank=True, null=True)
    mail_preference = models.CharField(max_length=1, blank=True, null=True)
    favourite_mailing_post = models.CharField(max_length=1, blank=True, null=True)
    member_entrance = models.CharField(max_length=4, blank=True, null=True)
    cell_phone = models.CharField(max_length=25, blank=True, null=True)
    logon_id = models.CharField(max_length=25, blank=True, null=True)
    logon_passwd = models.CharField(max_length=25, blank=True, null=True)
    course1 = models.CharField(max_length=2, blank=True, null=True)
    course2 = models.CharField(max_length=2, blank=True, null=True)
    print_received = models.CharField(max_length=1, blank=True, null=True)
    submitted_date = models.DateField(blank=True, null=True)
    last_updated_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, blank=True, null=True)
    logon_pass2 = models.CharField(max_length=128, blank=True, null=True)
    pass_reset_key = models.CharField(max_length=64, blank=True, null=True)
    pass_reset_exp = models.DateField(blank=True, null=True)
    last_changed = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'membership_applications_to_del'


class Multiplereservation(models.Model):
    res_id = models.FloatField()
    member_id = models.FloatField()
    resdate = models.DateField()
    created = models.DateField()
    modified = models.DateField()
    quantity1 = models.IntegerField()
    quantity2 = models.IntegerField()
    quantity3 = models.IntegerField()
    quantity4 = models.IntegerField()
    quantity5 = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'multiplereservation'


class Nationalities(models.Model):
    natid = models.CharField(max_length=2)
    ename = models.CharField(max_length=15, blank=True, null=True)
    fname = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'nationalities'


class NewmembersEmpty(models.Model):
    id = models.FloatField()
    name = models.CharField(max_length=25)
    firstname = models.CharField(max_length=25)
    birthday = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=2, blank=True, null=True)
    membership = models.CharField(max_length=2)
    lang = models.CharField(max_length=1, blank=True, null=True)
    category = models.CharField(max_length=1, blank=True, null=True)
    address1 = models.CharField(max_length=50, blank=True, null=True)
    address2 = models.CharField(max_length=50, blank=True, null=True)
    towncode = models.IntegerField(blank=True, null=True)
    town = models.CharField(max_length=25, blank=True, null=True)
    state = models.CharField(max_length=2, blank=True, null=True)
    phone1 = models.CharField(max_length=15, blank=True, null=True)
    phone2 = models.CharField(max_length=15, blank=True, null=True)
    cellphone = models.CharField(max_length=15, blank=True, null=True)
    e_mail = models.CharField(max_length=50, blank=True, null=True)
    mail_preference = models.CharField(max_length=1, blank=True, null=True)
    member_entrance = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'newmembers_empty'


class RMembers(models.Model):
    id = models.FloatField()
    r_id = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'r_members'


class RegattaParticipation(models.Model):
    id = models.FloatField(primary_key=True)
    member = models.ForeignKey(Members, models.DO_NOTHING)
    regatta = models.ForeignKey('RegattasExt', models.DO_NOTHING)
    boat = models.ForeignKey(Boats, models.DO_NOTHING, blank=True, null=True)
    preference = models.CharField(max_length=15)
    comments = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=15)
    report = models.CharField(max_length=4000, blank=True, null=True)
    report_photo_link = models.CharField(max_length=200, blank=True, null=True)
    report_date = models.DateField(blank=True, null=True)
    assigned_boat = models.ForeignKey(Boats, models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'regatta_participation'
        unique_together = (('member', 'regatta'),)


class RegattaProfiles(models.Model):
    id = models.FloatField(blank=True, null=True)
    member = models.ForeignKey(Members, models.DO_NOTHING)
    profile_year = models.IntegerField()
    licence = models.CharField(max_length=10, blank=True, null=True)
    club = models.CharField(max_length=25, blank=True, null=True)
    experience = models.CharField(max_length=1000)

    class Meta:
        managed = False
        db_table = 'regatta_profiles'


class RegattaSeriesExt(models.Model):
    id = models.FloatField(primary_key=True)
    name = models.CharField(max_length=50)
    url_rules = models.CharField(max_length=200, blank=True, null=True)
    url_web = models.CharField(max_length=200, blank=True, null=True)
    url_results = models.CharField(max_length=200, blank=True, null=True)
    year = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'regatta_series_ext'


class RegattasExt(models.Model):
    id = models.FloatField(primary_key=True)
    date_from = models.DateField()
    date_to = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=50)
    date_ycc_deadline = models.DateField(blank=True, null=True)
    date_reg_deadline = models.DateField(blank=True, null=True)
    ycc_boat_category = models.CharField(max_length=20)
    url_nor = models.CharField(max_length=200, blank=True, null=True)
    url_web = models.CharField(max_length=200, blank=True, null=True)
    url_results = models.CharField(max_length=200, blank=True, null=True)
    note = models.CharField(max_length=200, blank=True, null=True)
    boats_assigned = models.DateField(blank=True, null=True)
    url_si = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'regattas_ext'


class RegattasInSeries(models.Model):
    regatta_in_series_id = models.FloatField(primary_key=True)
    regatta = models.ForeignKey(RegattasExt, models.DO_NOTHING)
    series = models.ForeignKey(RegattaSeriesExt, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'regattas_in_series'
        unique_together = (('regatta', 'series'),)


class Reservations(models.Model):
    res_id = models.FloatField(primary_key=True)
    boat = models.ForeignKey(Boats, models.DO_NOTHING)
    owner_id = models.FloatField()
    label = models.CharField(max_length=25)
    day = models.DateField()
    period = models.BooleanField()
    locked = models.BooleanField(blank=True, null=True)
    deleted = models.DateField(blank=True, null=True)
    modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'reservations'


class Status(models.Model):
    stat_id = models.FloatField()
    boat = models.ForeignKey(Boats, models.DO_NOTHING)
    owner_id = models.FloatField()
    label = models.CharField(max_length=20)
    s_begin = models.DateField()
    s_end = models.DateField(blank=True, null=True)
    status = models.BooleanField()
    modified = models.DateField()

    class Meta:
        managed = False
        db_table = 'status'


class SuPreoutingLastentry2003Obs(models.Model):
    member_id = models.FloatField()
    year = models.IntegerField()
    comments = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'su_preouting_lastentry2003_obs'


class SutestLastentre2004Obs(models.Model):
    member_id = models.FloatField()
    theory = models.DateField(blank=True, null=True)
    tcomments = models.CharField(max_length=50, blank=True, null=True)
    practical = models.DateField(blank=True, null=True)
    pcomments = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sutest_lastentre2004_obs'


class SwsrecordsObsolete(models.Model):
    member_id = models.FloatField(blank=True, null=True)
    sws_year = models.IntegerField(blank=True, null=True)
    sent_to_sws_date = models.DateField(blank=True, null=True)
    comments = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'swsrecords_obsolete'


class SysTempFbt(models.Model):
    schema = models.CharField(max_length=32, blank=True, null=True)
    object_name = models.CharField(max_length=32, blank=True, null=True)
    object_field = models.FloatField(db_column='object#', blank=True, null=True)  # Field renamed to remove unsuitable characters. Field renamed because it ended with '_'.
    rid = models.TextField(blank=True, null=True)  # This field type is a guess.
    action = models.CharField(max_length=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sys_temp_fbt'


class TMembersObsolete(models.Model):
    t_id = models.FloatField()
    t_year = models.IntegerField()
    t_from = models.DateField(blank=True, null=True)
    t_to = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 't_members_obsolete'


class Teachers(models.Model):
    member_id = models.FloatField()
    license = models.CharField(max_length=5)
    active = models.BooleanField(blank=True, null=True)
    since = models.IntegerField(blank=True, null=True)
    teacher_id = models.FloatField(primary_key=True)

    class Meta:
        managed = False
        db_table = 'teachers'


class TempMembersLastentry2001Obs(models.Model):
    id = models.FloatField(blank=True, null=True)
    data = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=50, blank=True, null=True)
    membership = models.CharField(max_length=10, blank=True, null=True)
    paid_in = models.CharField(max_length=4, blank=True, null=True)
    fee = models.FloatField(blank=True, null=True)
    course = models.CharField(max_length=2, blank=True, null=True)
    course_cost = models.FloatField(blank=True, null=True)
    total = models.FloatField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'temp_members_lastentry2001_obs'


class TempmembersLastemtry2005Obs(models.Model):
    member_id = models.FloatField(blank=True, null=True)
    period_year = models.IntegerField(blank=True, null=True)
    period_from = models.CharField(max_length=3, blank=True, null=True)
    period_to = models.CharField(max_length=3, blank=True, null=True)
    months = models.BooleanField(blank=True, null=True)
    comments = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'tempmembers_lastemtry2005_obs'


class Tests(models.Model):
    test_id = models.FloatField(primary_key=True)
    test_type = models.CharField(max_length=5)
    member_id = models.FloatField()
    tester_id = models.FloatField()
    test_date = models.DateField()
    result = models.CharField(max_length=5)
    comments = models.TextField()

    class Meta:
        managed = False
        db_table = 'tests'


class ToDelLotteryBck20190207(models.Model):
    id = models.FloatField(blank=True, null=True)
    year = models.IntegerField()
    member_id = models.FloatField()
    course1 = models.CharField(max_length=2)
    course2 = models.CharField(max_length=2, blank=True, null=True)
    weekdays = models.CharField(max_length=21, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'to_del_lottery_bck20190207'


class Userlist(models.Model):
    username = models.CharField(unique=True, max_length=8, blank=True, null=True)
    password = models.CharField(max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'userlist'


class WebLogon(models.Model):
    member = models.OneToOneField(Members, models.DO_NOTHING, primary_key=True)
    logon_id = models.CharField(unique=True, max_length=25)
    session_id = models.FloatField(blank=True, null=True)
    session_date = models.DateField(blank=True, null=True)
    logon_pass2 = models.CharField(max_length=128, blank=True, null=True)
    pass_reset_key = models.CharField(max_length=128, blank=True, null=True)
    pass_reset_exp = models.DateField(blank=True, null=True)
    last_changed = models.DateField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'web_logon'


class WebLogonAudit(models.Model):
    logon_id = models.CharField(max_length=50, blank=True, null=True)
    session_id = models.CharField(max_length=50, blank=True, null=True)
    client_ip = models.CharField(max_length=50, blank=True, null=True)
    event_datetime = models.DateField(blank=True, null=True)
    event_type = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'web_logon_audit'


class WebnewsEmpty(models.Model):
    submitter = models.FloatField()
    submitter_email = models.CharField(max_length=50)
    submission = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    message_type = models.CharField(max_length=10, blank=True, null=True)
    message = models.CharField(max_length=500)
    message_url = models.CharField(max_length=100, blank=True, null=True)
    image_url = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'webnews_empty'


class Ycclog(models.Model):
    boat = models.ForeignKey(Boats, models.DO_NOTHING)
    owner = models.ForeignKey(Members, models.DO_NOTHING)
    status = models.CharField(max_length=10)
    modified = models.DateField(primary_key=True)
    keyslog_id = models.FloatField(blank=True, null=True)
    log_id = models.FloatField()
    log_comment = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ycclog'
