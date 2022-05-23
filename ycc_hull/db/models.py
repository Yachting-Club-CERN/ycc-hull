# Generated at 2022-05-23 at 21:18 from February 2022 local Oracle DB
# Then manually modified
from sqlalchemy import CHAR, CheckConstraint, Column, DateTime, ForeignKeyConstraint, Index, Integer, LargeBinary, PrimaryKeyConstraint, TIMESTAMP, Table, Text, VARCHAR, text
from sqlalchemy.dialects.oracle import NUMBER
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
metadata = Base.metadata


t_admin = Table(
    'admin', metadata,
    Column('member_id', Integer, nullable=False, unique=True),
    Column('rights', NUMBER(asdecimal=False)),
    Column('modified', DateTime),
    Column('comments', VARCHAR(100)),
    Index('adminindex1', 'member_id', unique=True)
)


t_admin_values = Table(
    'admin_values', metadata,
    Column('right', VARCHAR(20)),
    Column('value', NUMBER(2, 0, False))
)


t_agenda_empty = Table(
    'agenda_empty', metadata,
    Column('day', DateTime, nullable=False),
    Column('start_time', DateTime),
    Column('end_time', DateTime),
    Column('submitter', NUMBER(asdecimal=False), nullable=False),
    Column('type', VARCHAR(20), nullable=False),
    Column('title', VARCHAR(100), nullable=False),
    Column('place', VARCHAR(100)),
    Column('text', VARCHAR(500)),
    Column('url', VARCHAR(100)),
    Column('image_url', VARCHAR(100))
)


t_ba5_obsolete = Table(
    'ba5_obsolete', metadata,
    Column('id', NUMBER(2, 0, False), nullable=False),
    Column('prefix', VARCHAR(20)),
    Column('name', VARCHAR(6)),
    Column('comments', VARCHAR(22))
)


class BoatKeys(Base):
    __tablename__ = 'boat_keys'
    __table_args__ = (
        PrimaryKeyConstraint('boat_id', name='boat_keys_pk'),
    )

    boat_id = Column(NUMBER(3, 0, False))
    key_nr = Column(NUMBER(3, 0, False), nullable=False)
    locked = Column(NUMBER(1, 0, False))
    virtual = Column(NUMBER(1, 0, False))


class Buvette(Base):
    __tablename__ = 'buvette'
    __table_args__ = (
        PrimaryKeyConstraint('res_id', name='sys_c008367'),
    )

    res_id = Column(NUMBER(asdecimal=False))
    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    day = Column(DateTime, nullable=False)
    quantity = Column(NUMBER(2, 0, False), nullable=False)
    modified = Column(DateTime, nullable=False)
    menu = Column(NUMBER(1, 0, False))


class Countries(Base):
    __tablename__ = 'countries'
    __table_args__ = (
        PrimaryKeyConstraint('country_code', name='sys_c008338'),
    )

    country_name = Column(VARCHAR(50), nullable=False)
    country_code = Column(VARCHAR(2))


class DeletedMemberApps(Base):
    __tablename__ = 'deleted_member_apps'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008493'),
    )

    id = Column(NUMBER(asdecimal=False))
    name = Column(VARCHAR(25), nullable=False)
    firstname = Column(VARCHAR(25), nullable=False)


class EmailQueueTable(Base):
    __tablename__ = 'email_queue_table'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008395'),
    )

    id = Column(NUMBER(6, 0, False))
    from_field = Column(VARCHAR(100))
    to_field = Column(VARCHAR(4000))
    subject = Column(VARCHAR(200))
    body = Column(VARCHAR(4000))
    status = Column(VARCHAR(20), index=True)
    time_stamp = Column(TIMESTAMP, server_default=text('systimestamp'))
    cc_field = Column(VARCHAR(4000))


t_email_templates = Table(
    'email_templates', metadata,
    Column('id', NUMBER(4, 0, False)),
    Column('body', VARCHAR(4000)),
    Column('description', VARCHAR(60))
)


class EntranceFeesrecords(Base):
    __tablename__ = 'entrance_feesrecords'
    __table_args__ = (
        PrimaryKeyConstraint('member_id', name='entrance_feesrecords_pk'),
        Index('entrance_fee_uq', 'member_id', 'year_f', unique=True)
    )

    member_id = Column(NUMBER(asdecimal=False))
    year_f = Column(NUMBER(asdecimal=False))


class Fees(Base):
    __tablename__ = 'fees'
    __table_args__ = (
        CheckConstraint("cat_id in ('AS','AJ','FM','H','C','T')", name='check_cat'),
        PrimaryKeyConstraint('cat_id', name='cat_pk')
    )

    cat_id = Column(VARCHAR(2))
    description = Column(VARCHAR(25), nullable=False)
    entrance_fee = Column(NUMBER(asdecimal=False), nullable=False)
    annual_fee = Column(NUMBER(asdecimal=False), nullable=False)
    lastchange = Column(VARCHAR(15))


t_feescourses_lastentry2005_obs = Table(
    'feescourses_lastentry2005_obs', metadata,
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('year_c', NUMBER(4, 0, False), nullable=False),
    Column('course', VARCHAR(2), nullable=False),
    Column('paid_date', DateTime),
    Column('paid_mode', VARCHAR(4)),
    Column('feecourse', NUMBER(3, 0, False), nullable=False)
)


t_feesrecords = Table(
    'feesrecords', metadata,
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('year_f', NUMBER(4, 0, False), nullable=False),
    Column('paid_date', DateTime),
    Column('paid_mode', VARCHAR(4)),
    Column('fee', NUMBER(3, 0, False), nullable=False),
    Column('entered_date', DateTime, server_default=text('sysdate')),
    Column('paymentid', NUMBER(asdecimal=False))
)


t_holidays = Table(
    'holidays', metadata,
    Column('day', DateTime, nullable=False),
    Column('label', VARCHAR(20), nullable=False)
)


class ImportantDates(Base):
    __tablename__ = 'important_dates'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008460'),
    )

    id = Column(NUMBER(asdecimal=False))
    what = Column(VARCHAR(50), nullable=False, unique=True)
    datetime = Column(DateTime)


class ImportantValues(Base):
    __tablename__ = 'important_values'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008326'),
    )

    id = Column(NUMBER(10, 0, False))
    what = Column(VARCHAR(50), nullable=False)
    val = Column(VARCHAR(50), nullable=False)
    last_modified = Column(DateTime, nullable=False)


class Infolicences(Base):
    __tablename__ = 'infolicences'
    __table_args__ = (
        PrimaryKeyConstraint('infoid', name='licinfo_pk'),
    )

    infoid = Column(NUMBER(asdecimal=False))
    description = Column(VARCHAR(50), nullable=False)
    ncourse = Column(VARCHAR(2))
    nlicence = Column(VARCHAR(2))
    nkey = Column(VARCHAR(2))
    coursefee = Column(NUMBER(4, 0, False))
    course_name = Column(VARCHAR(30))
    course_active = Column(CHAR(1))
    course_level = Column(NUMBER(1, 0, False))


class Lottery(Base):
    __tablename__ = 'lottery'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008503'),
        Index('lottery_uq', 'year', 'member_id', unique=True)
    )

    id = Column(NUMBER(asdecimal=False))
    year = Column(NUMBER(4, 0, False), nullable=False)
    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    course1 = Column(VARCHAR(2))
    course2 = Column(VARCHAR(2))
    weekdays = Column(VARCHAR(21))
    level0 = Column(VARCHAR(1))


class LotteryPlaces(Base):
    __tablename__ = 'lottery_places'
    __table_args__ = (
        PrimaryKeyConstraint('key', name='sys_c008509'),
    )

    key = Column(VARCHAR(2))
    places = Column(NUMBER(asdecimal=False))


class LotteryResults(Base):
    __tablename__ = 'lottery_results'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008423'),
        Index('lottery_results_uq1', 'member_id', 'year', unique=True),
        Index('lottery_results_uq2', 'drawn_seq', 'year', unique=True)
    )

    id = Column(NUMBER(asdecimal=False))
    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    year = Column(NUMBER(4, 0, False), nullable=False, server_default=text('extract(year from sysdate)'))
    drawn_seq = Column(NUMBER(asdecimal=False), nullable=False)
    withdrawn = Column(VARCHAR(1))
    wd_comment = Column(VARCHAR(1000))
    course_day = Column(VARCHAR(25))


t_lottery_results_archive = Table(
    'lottery_results_archive', metadata,
    Column('id', NUMBER(asdecimal=False)),
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('year', NUMBER(4, 0, False), nullable=False),
    Column('drawn_seq', NUMBER(asdecimal=False), nullable=False),
    Column('withdrawn', VARCHAR(1)),
    Column('wd_comment', VARCHAR(1000)),
    Column('course_day', VARCHAR(25))
)


class Members(Base):
    __tablename__ = 'members'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='members_pk'),
    )

    id = Column(NUMBER(asdecimal=False))
    name = Column(VARCHAR(25), nullable=False)
    firstname = Column(VARCHAR(25), nullable=False)
    membership = Column(VARCHAR(2), nullable=False)
    home_addr = Column(VARCHAR(50), nullable=False)
    member_entrance = Column(VARCHAR(4), nullable=False)
    birthday = Column(DateTime)
    nationality = Column(VARCHAR(3))
    temp_memb = Column(NUMBER(1, 0, False))
    lang1 = Column(VARCHAR(3))
    lang2 = Column(VARCHAR(3))
    category = Column(VARCHAR(1))
    work_address1 = Column(VARCHAR(50))
    work_address2 = Column(VARCHAR(50))
    work_towncode = Column(VARCHAR(7))
    work_town = Column(VARCHAR(25))
    work_state = Column(VARCHAR(5))
    work_phone = Column(VARCHAR(25))
    e_mail = Column(VARCHAR(50))
    home_towncode = Column(VARCHAR(7))
    home_town = Column(VARCHAR(25))
    home_state = Column(VARCHAR(5))
    home_phone = Column(VARCHAR(25))
    mail_preference = Column(VARCHAR(1))
    favourite_mailing_post = Column(VARCHAR(1))
    cell_phone = Column(VARCHAR(25))
    gender = Column(CHAR(1))
    valid_until_date = Column(DateTime)
    last_updated_date = Column(DateTime)
    valid_from_date = Column(DateTime)

    boats = relationship('Boats', back_populates='members')
    committee = relationship('Committee', back_populates='member')
    courses_obs = relationship('CoursesObs', back_populates='member')
    keys = relationship('Keys', back_populates='member')
    licences = relationship('Licences', back_populates='member')
    regatta_participation = relationship('RegattaParticipation', back_populates='member')
    ycclog = relationship('Ycclog', back_populates='owner')


class MembersXxEmpty(Base):
    __tablename__ = 'members_xx_empty'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='members_xx_pk'),
    )

    id = Column(NUMBER(asdecimal=False))
    name = Column(VARCHAR(25), nullable=False)
    firstname = Column(VARCHAR(25), nullable=False)
    membership = Column(VARCHAR(2), nullable=False)
    member_entrance = Column(VARCHAR(2), nullable=False)
    birthday = Column(DateTime)
    nationality = Column(VARCHAR(3))
    pref_lang = Column(VARCHAR(1))
    lang2 = Column(VARCHAR(1))
    category = Column(VARCHAR(1))
    resid = Column(VARCHAR(2))
    address1 = Column(VARCHAR(50))
    address2 = Column(VARCHAR(50))
    towncode = Column(VARCHAR(7))
    town = Column(VARCHAR(25))
    state = Column(VARCHAR(2))
    work_phone = Column(VARCHAR(20))
    home_phone = Column(VARCHAR(20))
    cell_phone = Column(VARCHAR(20))
    e_mail = Column(VARCHAR(50))
    mail_preference = Column(VARCHAR(1))


t_membership = Table(
    'membership', metadata,
    Column('mb_id', NUMBER(2, 0, False), nullable=False),
    Column('mb_name', VARCHAR(2), nullable=False),
    Column('e_desc', VARCHAR(20), nullable=False),
    Column('f_desc', VARCHAR(20), nullable=False),
    Column('comments', VARCHAR(100))
)


class MembershipApplications(Base):
    __tablename__ = 'membership_applications'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='applications_pk'),
    )

    id = Column(NUMBER(asdecimal=False))
    name = Column(VARCHAR(25), nullable=False)
    firstname = Column(VARCHAR(25), nullable=False)
    birthday = Column(DateTime, nullable=False)
    membership = Column(VARCHAR(2), nullable=False)
    category = Column(VARCHAR(1), nullable=False)
    nationality = Column(VARCHAR(3))
    temp_memb = Column(NUMBER(1, 0, False))
    lang1 = Column(VARCHAR(3))
    lang2 = Column(VARCHAR(3))
    work_address1 = Column(VARCHAR(50))
    work_address2 = Column(VARCHAR(50))
    work_towncode = Column(VARCHAR(7))
    work_town = Column(VARCHAR(25))
    work_state = Column(VARCHAR(5))
    work_phone = Column(VARCHAR(25))
    e_mail = Column(VARCHAR(50))
    home_addr = Column(VARCHAR(50))
    home_towncode = Column(VARCHAR(7))
    home_town = Column(VARCHAR(25))
    home_state = Column(VARCHAR(5))
    home_phone = Column(VARCHAR(25))
    mail_preference = Column(VARCHAR(1))
    favourite_mailing_post = Column(VARCHAR(1))
    member_entrance = Column(VARCHAR(4))
    cell_phone = Column(VARCHAR(25))
    logon_id = Column(VARCHAR(25), unique=True)
    logon_passwd = Column(VARCHAR(25))
    course1 = Column(VARCHAR(2))
    course2 = Column(VARCHAR(2))
    print_received = Column(CHAR(1), server_default=text("'N'"))
    submitted_date = Column(DateTime, server_default=text('sysdate'))
    last_updated_date = Column(DateTime)
    gender = Column(CHAR(1))
    logon_pass2 = Column(VARCHAR(128))
    pass_reset_key = Column(VARCHAR(64))
    pass_reset_exp = Column(DateTime)
    last_changed = Column(DateTime)


t_membership_applications_to_del = Table(
    'membership_applications_to_del', metadata,
    Column('id', NUMBER(asdecimal=False), nullable=False),
    Column('name', VARCHAR(25), nullable=False),
    Column('firstname', VARCHAR(25), nullable=False),
    Column('birthday', DateTime, nullable=False),
    Column('nationality', VARCHAR(3)),
    Column('membership', VARCHAR(2), nullable=False),
    Column('temp_memb', NUMBER(1, 0, False)),
    Column('lang1', VARCHAR(3)),
    Column('lang2', VARCHAR(3)),
    Column('category', VARCHAR(1), nullable=False),
    Column('work_address1', VARCHAR(50)),
    Column('work_address2', VARCHAR(50)),
    Column('work_towncode', VARCHAR(7)),
    Column('work_town', VARCHAR(25)),
    Column('work_state', VARCHAR(5)),
    Column('work_phone', VARCHAR(25)),
    Column('e_mail', VARCHAR(50)),
    Column('home_addr', VARCHAR(50)),
    Column('home_towncode', VARCHAR(7)),
    Column('home_town', VARCHAR(25)),
    Column('home_state', VARCHAR(5)),
    Column('home_phone', VARCHAR(25)),
    Column('mail_preference', VARCHAR(1)),
    Column('favourite_mailing_post', VARCHAR(1)),
    Column('member_entrance', VARCHAR(4)),
    Column('cell_phone', VARCHAR(25)),
    Column('logon_id', VARCHAR(25)),
    Column('logon_passwd', VARCHAR(25)),
    Column('course1', VARCHAR(2)),
    Column('course2', VARCHAR(2)),
    Column('print_received', CHAR(1)),
    Column('submitted_date', DateTime),
    Column('last_updated_date', DateTime),
    Column('gender', CHAR(1)),
    Column('logon_pass2', VARCHAR(128)),
    Column('pass_reset_key', VARCHAR(64)),
    Column('pass_reset_exp', DateTime),
    Column('last_changed', DateTime)
)


t_multiplereservation = Table(
    'multiplereservation', metadata,
    Column('res_id', NUMBER(asdecimal=False), nullable=False),
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('resdate', DateTime, nullable=False),
    Column('created', DateTime, nullable=False),
    Column('modified', DateTime, nullable=False),
    Column('quantity1', NUMBER(2, 0, False), nullable=False),
    Column('quantity2', NUMBER(2, 0, False), nullable=False),
    Column('quantity3', NUMBER(2, 0, False), nullable=False),
    Column('quantity4', NUMBER(2, 0, False), nullable=False),
    Column('quantity5', NUMBER(2, 0, False), server_default=text('0\n   '))
)


t_nationalities = Table(
    'nationalities', metadata,
    Column('natid', VARCHAR(2), nullable=False),
    Column('ename', VARCHAR(15)),
    Column('fname', VARCHAR(15))
)


t_newmembers_empty = Table(
    'newmembers_empty', metadata,
    Column('id', NUMBER(asdecimal=False), nullable=False),
    Column('name', VARCHAR(25), nullable=False),
    Column('firstname', VARCHAR(25), nullable=False),
    Column('birthday', DateTime),
    Column('nationality', VARCHAR(2)),
    Column('membership', VARCHAR(2), nullable=False),
    Column('lang', VARCHAR(1)),
    Column('category', VARCHAR(1)),
    Column('address1', VARCHAR(50)),
    Column('address2', VARCHAR(50)),
    Column('towncode', NUMBER(7, 0, False)),
    Column('town', VARCHAR(25)),
    Column('state', VARCHAR(2)),
    Column('phone1', VARCHAR(15)),
    Column('phone2', VARCHAR(15)),
    Column('cellphone', VARCHAR(15)),
    Column('e_mail', VARCHAR(50)),
    Column('mail_preference', VARCHAR(1)),
    Column('member_entrance', NUMBER(4, 0, False), nullable=False)
)


t_r_members = Table(
    'r_members', metadata,
    Column('id', NUMBER(asdecimal=False), nullable=False),
    Column('r_id', NUMBER(asdecimal=False))
)


class RegattaSeriesExt(Base):
    __tablename__ = 'regatta_series_ext'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008398'),
    )

    id = Column(NUMBER(asdecimal=False))
    name = Column(VARCHAR(50), nullable=False)
    year = Column(NUMBER(4, 0, False), nullable=False)
    url_rules = Column(VARCHAR(200))
    url_web = Column(VARCHAR(200))
    url_results = Column(VARCHAR(200))

    regattas_in_series = relationship('RegattasInSeries', back_populates='series')


class RegattasExt(Base):
    __tablename__ = 'regattas_ext'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='sys_c008361'),
    )

    id = Column(NUMBER(asdecimal=False))
    date_from = Column(DateTime, nullable=False, index=True)
    name = Column(VARCHAR(50), nullable=False)
    ycc_boat_category = Column(VARCHAR(20), nullable=False)
    date_to = Column(DateTime)
    date_ycc_deadline = Column(DateTime)
    date_reg_deadline = Column(DateTime)
    url_nor = Column(VARCHAR(200))
    url_web = Column(VARCHAR(200))
    url_results = Column(VARCHAR(200))
    note = Column(VARCHAR(200))
    boats_assigned = Column(DateTime)
    url_si = Column(VARCHAR(200))

    regattas_in_series = relationship('RegattasInSeries', back_populates='regatta')
    regatta_participation = relationship('RegattaParticipation', back_populates='regatta')


t_su_preouting_lastentry2003_obs = Table(
    'su_preouting_lastentry2003_obs', metadata,
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('year', NUMBER(4, 0, False), nullable=False),
    Column('comments', VARCHAR(50))
)


t_sutest_lastentre2004_obs = Table(
    'sutest_lastentre2004_obs', metadata,
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('theory', DateTime),
    Column('tcomments', VARCHAR(50)),
    Column('practical', DateTime),
    Column('pcomments', VARCHAR(50))
)


t_swsrecords_obsolete = Table(
    'swsrecords_obsolete', metadata,
    Column('member_id', NUMBER(asdecimal=False)),
    Column('sws_year', NUMBER(4, 0, False)),
    Column('sent_to_sws_date', DateTime),
    Column('comments', VARCHAR(20))
)


t_t_members_obsolete = Table(
    't_members_obsolete', metadata,
    Column('t_id', NUMBER(asdecimal=False), nullable=False),
    Column('t_year', NUMBER(4, 0, False), nullable=False),
    Column('t_from', DateTime),
    Column('t_to', DateTime)
)


class Teachers(Base):
    __tablename__ = 'teachers'
    __table_args__ = (
        PrimaryKeyConstraint('teacher_id', name='sys_c008428'),
    )

    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    license = Column(VARCHAR(5), nullable=False)
    teacher_id = Column(NUMBER(asdecimal=False))
    active = Column(NUMBER(1, 0, False))
    since = Column(NUMBER(4, 0, False))


t_temp_members_lastentry2001_obs = Table(
    'temp_members_lastentry2001_obs', metadata,
    Column('id', NUMBER(asdecimal=False)),
    Column('data', DateTime),
    Column('name', VARCHAR(50)),
    Column('membership', VARCHAR(10)),
    Column('paid_in', VARCHAR(4)),
    Column('fee', NUMBER(asdecimal=False)),
    Column('course', VARCHAR(2)),
    Column('course_cost', NUMBER(asdecimal=False)),
    Column('total', NUMBER(asdecimal=False))
)


t_tempmembers_lastemtry2005_obs = Table(
    'tempmembers_lastemtry2005_obs', metadata,
    Column('member_id', NUMBER(asdecimal=False)),
    Column('period_year', NUMBER(4, 0, False)),
    Column('period_from', VARCHAR(3)),
    Column('period_to', VARCHAR(3)),
    Column('months', NUMBER(1, 0, False)),
    Column('comments', VARCHAR(50))
)


class Tests(Base):
    __tablename__ = 'tests'
    __table_args__ = (
        PrimaryKeyConstraint('test_id', name='sys_c008346'),
    )

    test_id = Column(NUMBER(asdecimal=False))
    test_type = Column(VARCHAR(5), nullable=False)
    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    tester_id = Column(NUMBER(asdecimal=False), nullable=False)
    test_date = Column(DateTime, nullable=False)
    result = Column(VARCHAR(5), nullable=False)
    comments = Column(Text, nullable=False)


t_to_del_lottery_bck20190207 = Table(
    'to_del_lottery_bck20190207', metadata,
    Column('id', NUMBER(asdecimal=False)),
    Column('year', NUMBER(4, 0, False), nullable=False),
    Column('member_id', NUMBER(asdecimal=False), nullable=False),
    Column('course1', VARCHAR(2), nullable=False),
    Column('course2', VARCHAR(2)),
    Column('weekdays', VARCHAR(21))
)


t_userlist = Table(
    'userlist', metadata,
    Column('username', VARCHAR(8), unique=True),
    Column('password', VARCHAR(10)),
    Index('sys_c008429', 'username', unique=True)
)


t_web_logon_audit = Table(
    'web_logon_audit', metadata,
    Column('logon_id', VARCHAR(50)),
    Column('session_id', VARCHAR(50)),
    Column('client_ip', VARCHAR(50)),
    Column('event_datetime', DateTime),
    Column('event_type', VARCHAR(30))
)


t_webnews_empty = Table(
    'webnews_empty', metadata,
    Column('submitter', NUMBER(asdecimal=False), nullable=False),
    Column('submitter_email', VARCHAR(50), nullable=False),
    Column('submission', DateTime, nullable=False),
    Column('expiry_date', DateTime),
    Column('message_type', VARCHAR(10)),
    Column('message', VARCHAR(500), nullable=False),
    Column('message_url', VARCHAR(100)),
    Column('image_url', VARCHAR(100))
)


t_ba5assign_obsolete = Table(
    'ba5assign_obsolete', metadata,
    Column('keyid', NUMBER(2, 0, False)),
    Column('member_id', NUMBER(6, 0, False)),
    Column('assigned_date', DateTime),
    Column('return_date', DateTime),
    Column('comments', VARCHAR(50)),
    Column('last_verif', DateTime),
    ForeignKeyConstraint(['member_id'], ['members.id'], name='ba5ass_member_id_fk')
)


class Boats(Base):
    __tablename__ = 'boats'
    __table_args__ = (
        ForeignKeyConstraint(['maintainer_id2'], ['members.id'], name='sys_c008532'),
        PrimaryKeyConstraint('boat_id', name='sys_c008447')
    )

    boat_id = Column(NUMBER(3, 0, False))
    name = Column(VARCHAR(20), nullable=False, unique=True)
    type = Column(VARCHAR(20), nullable=False)
    ycc_num = Column(NUMBER(3, 0, False), nullable=False, unique=True)
    license = Column(VARCHAR(5), nullable=False)
    class_ = Column('class', VARCHAR(5), nullable=False)
    table_pos = Column(NUMBER(3, 0, False), nullable=False, unique=True)
    maintainer_id = Column(NUMBER(asdecimal=False))
    ext_reg_cat = Column(VARCHAR(2))
    maintainer_id2 = Column(NUMBER(asdecimal=False))
    registration_pdf = Column(LargeBinary)

    members = relationship('Members', back_populates='boats')
    keyslog = relationship('Keyslog', back_populates='boat')
    regatta_participation = relationship('RegattaParticipation', foreign_keys='[RegattaParticipation.assigned_boat_id]', back_populates='assigned_boat')
    regatta_participation_ = relationship('RegattaParticipation', foreign_keys='[RegattaParticipation.boat_id]', back_populates='boat')
    reservations = relationship('Reservations', back_populates='boat')
    ycclog = relationship('Ycclog', back_populates='boat')


t_classes_obsolete2001 = Table(
    'classes_obsolete2001', metadata,
    Column('class_id', NUMBER(asdecimal=False), nullable=False),
    Column('course_id', NUMBER(2, 0, False), nullable=False),
    Column('teacher_id', NUMBER(asdecimal=False), nullable=False),
    Column('helper_id', NUMBER(asdecimal=False)),
    Column('course_year', NUMBER(4, 0, False), nullable=False),
    Column('day_class', VARCHAR(3)),
    Column('lang', VARCHAR(2)),
    Column('notes', VARCHAR(50)),
    ForeignKeyConstraint(['helper_id'], ['members.id'], name='helper_fk'),
    ForeignKeyConstraint(['teacher_id'], ['members.id'], name='teacher_fk'),
    Index('classes_pk', 'class_id', 'teacher_id', 'course_year', unique=True)
)


class Committee(Base):
    __tablename__ = 'committee'
    __table_args__ = (
        ForeignKeyConstraint(['member_id'], ['members.id'], name='committee_member_fk'),
        PrimaryKeyConstraint('member_id', 'cyear', name='committee_pk')
    )

    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    cyear = Column(NUMBER(4, 0, False), nullable=False)
    commid = Column(NUMBER(10, 0, False), nullable=False)
    lcomments = Column(VARCHAR(100))
    photo = Column(VARCHAR(50))
    position = Column(NUMBER(asdecimal=False))
    roles = Column(VARCHAR(500))

    member = relationship('Members', back_populates='committee')


class CoursesObs(Base):
    __tablename__ = 'courses_obs'
    __table_args__ = (
        ForeignKeyConstraint(['member_id'], ['members.id'], name='member_fk'),
        PrimaryKeyConstraint('member_id', 'class_id', name='courses_pk')
    )

    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    class_id = Column(NUMBER(asdecimal=False), nullable=False)
    pref_days = Column(VARCHAR(20))
    pref_lang = Column(VARCHAR(10))
    notes = Column(VARCHAR(50))

    member = relationship('Members', back_populates='courses_obs')


class Keys(Base):
    __tablename__ = 'keys'
    __table_args__ = (
        ForeignKeyConstraint(['member_id'], ['members.id'], name='sys_c008537'),
        PrimaryKeyConstraint('key_id', 'member_id', 'kyear', name='keys_pk')
    )

    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    key_id = Column(NUMBER(asdecimal=False), nullable=False)
    kyear = Column(NUMBER(asdecimal=False), nullable=False)

    member = relationship('Members', back_populates='keys')


class Licences(Base):
    __tablename__ = 'licences'
    __table_args__ = (
        ForeignKeyConstraint(['member_id'], ['members.id'], name='sys_c008539'),
        PrimaryKeyConstraint('licence_id', 'member_id', name='licence_pk')
    )

    member_id = Column(NUMBER(asdecimal=False), nullable=False)
    licence_id = Column(NUMBER(2, 0, False), nullable=False)
    lyear = Column(NUMBER(4, 0, False), nullable=False)
    lcomments = Column(VARCHAR(100))
    test_id = Column(NUMBER(asdecimal=False))
    status = Column(NUMBER(4, 0, False))

    member = relationship('Members', back_populates='licences')


t_regatta_profiles = Table(
    'regatta_profiles', metadata,
    Column('id', NUMBER(asdecimal=False)),
    Column('member_id', NUMBER(asdecimal=False), nullable=False, index=True),
    Column('profile_year', NUMBER(4, 0, False), nullable=False),
    Column('licence', VARCHAR(10)),
    Column('club', VARCHAR(25)),
    Column('experience', VARCHAR(1000), nullable=False),
    ForeignKeyConstraint(['member_id'], ['members.id'], name='sys_c008546'),
    Index('ref_prof_mem_id', 'member_id')
)


class RegattasInSeries(Base):
    __tablename__ = 'regattas_in_series'
    __table_args__ = (
        ForeignKeyConstraint(['regatta_id'], ['regattas_ext.id'], name='sys_c008540'),
        ForeignKeyConstraint(['series_id'], ['regatta_series_ext.id'], name='sys_c008541'),
        PrimaryKeyConstraint('regatta_in_series_id', name='sys_c008402'),
        Index('regattas_in_series_uq', 'regatta_id', 'series_id', unique=True)
    )

    regatta_in_series_id = Column(NUMBER(asdecimal=False))
    regatta_id = Column(NUMBER(asdecimal=False), nullable=False)
    series_id = Column(NUMBER(asdecimal=False), nullable=False)

    regatta = relationship('RegattasExt', back_populates='regattas_in_series')
    series = relationship('RegattaSeriesExt', back_populates='regattas_in_series')


class WebLogon(Members):
    __tablename__ = 'web_logon'
    __table_args__ = (
        ForeignKeyConstraint(['member_id'], ['members.id'], name='sys_c008549'),
        PrimaryKeyConstraint('member_id', name='sys_c008499')
    )

    member_id = Column(NUMBER(asdecimal=False))
    logon_id = Column(VARCHAR(25), nullable=False, unique=True)
    session_id = Column(NUMBER(asdecimal=False))
    session_date = Column(DateTime)
    logon_pass2 = Column(VARCHAR(128))
    pass_reset_key = Column(VARCHAR(128))
    pass_reset_exp = Column(DateTime)
    last_changed = Column(DateTime)


class Keyslog(Base):
    __tablename__ = 'keyslog'
    __table_args__ = (
        ForeignKeyConstraint(['boat_id'], ['boats.boat_id'], name='sys_c008538'),
        PrimaryKeyConstraint('keyslog_id', name='sys_c008458')
    )

    keyslog_id = Column(NUMBER(asdecimal=False))
    boat_id = Column(NUMBER(3, 0, False), nullable=False)
    taken_by = Column(NUMBER(asdecimal=False), nullable=False)
    taken = Column(DateTime, nullable=False)
    returned_by = Column(NUMBER(asdecimal=False))
    returned = Column(DateTime)
    log_id = Column(NUMBER(asdecimal=False))

    boat = relationship('Boats', back_populates='keyslog')


class RegattaParticipation(Base):
    __tablename__ = 'regatta_participation'
    __table_args__ = (
        ForeignKeyConstraint(['assigned_boat_id'], ['boats.boat_id'], name='sys_c008542'),
        ForeignKeyConstraint(['boat_id'], ['boats.boat_id'], name='sys_c008545'),
        ForeignKeyConstraint(['member_id'], ['members.id'], name='sys_c008543'),
        ForeignKeyConstraint(['regatta_id'], ['regattas_ext.id'], name='sys_c008544'),
        PrimaryKeyConstraint('id', name='sys_c008321'),
        Index('regatta_particip_uq', 'member_id', 'regatta_id', unique=True)
    )

    id = Column(NUMBER(asdecimal=False))
    member_id = Column(NUMBER(asdecimal=False), nullable=False, index=True)
    regatta_id = Column(NUMBER(asdecimal=False), nullable=False, index=True)
    preference = Column(VARCHAR(15), nullable=False)
    status = Column(VARCHAR(15), nullable=False, server_default=text("'Submitted'"))
    boat_id = Column(NUMBER(asdecimal=False))
    comments = Column(VARCHAR(200))
    report = Column(VARCHAR(4000))
    report_photo_link = Column(VARCHAR(200))
    report_date = Column(DateTime)
    assigned_boat_id = Column(NUMBER(asdecimal=False))

    assigned_boat = relationship('Boats', foreign_keys=[assigned_boat_id], back_populates='regatta_participation')
    boat = relationship('Boats', foreign_keys=[boat_id], back_populates='regatta_participation_')
    member = relationship('Members', back_populates='regatta_participation')
    regatta = relationship('RegattasExt', back_populates='regatta_participation')


class Reservations(Base):
    __tablename__ = 'reservations'
    __table_args__ = (
        ForeignKeyConstraint(['boat_id'], ['boats.boat_id'], name='sys_c008547'),
        PrimaryKeyConstraint('res_id', name='sys_c008481')
    )

    res_id = Column(NUMBER(asdecimal=False))
    boat_id = Column(NUMBER(3, 0, False), nullable=False)
    owner_id = Column(NUMBER(asdecimal=False), nullable=False)
    label = Column(VARCHAR(25), nullable=False)
    day = Column(DateTime, nullable=False)
    period = Column(NUMBER(1, 0, False), nullable=False)
    modified = Column(DateTime, nullable=False)
    locked = Column(NUMBER(1, 0, False))
    deleted = Column(DateTime)

    boat = relationship('Boats', back_populates='reservations')


t_status = Table(
    'status', metadata,
    Column('stat_id', NUMBER(asdecimal=False), nullable=False),
    Column('boat_id', NUMBER(3, 0, False), nullable=False),
    Column('owner_id', NUMBER(asdecimal=False), nullable=False),
    Column('label', VARCHAR(20), nullable=False),
    Column('s_begin', DateTime, nullable=False),
    Column('s_end', DateTime),
    Column('status', NUMBER(1, 0, False), nullable=False),
    Column('modified', DateTime, nullable=False),
    ForeignKeyConstraint(['boat_id'], ['boats.boat_id'], name='sys_c008548')
)


class Ycclog(Base):
    __tablename__ = 'ycclog'
    __table_args__ = (
        ForeignKeyConstraint(['boat_id'], ['boats.boat_id'], name='sys_c008550'),
        ForeignKeyConstraint(['owner_id'], ['members.id'], name='sys_c008551'),
        PrimaryKeyConstraint('modified', name='sys_c008523')
    )

    boat_id = Column(NUMBER(3, 0, False), nullable=False)
    owner_id = Column(NUMBER(asdecimal=False), nullable=False)
    status = Column(VARCHAR(10), nullable=False)
    modified = Column(DateTime)
    log_id = Column(NUMBER(asdecimal=False), nullable=False)
    keyslog_id = Column(NUMBER(asdecimal=False))
    log_comment = Column(Text)

    boat = relationship('Boats', back_populates='ycclog')
    owner = relationship('Members', back_populates='ycclog')
