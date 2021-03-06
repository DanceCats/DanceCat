"""
Docstring for DanceCats.Forms module.

Contains the forms classes which is extended from
WTForms. Used for template's forms rendering.
"""

from flask_wtf import Form
from wtforms import StringField, PasswordField, TextAreaField, \
    SelectField, IntegerField, \
    BooleanField, HiddenField, \
    FormField, FieldList, \
    validators
from wtforms.compat import iteritems
from . import Constants, config


class RegisterForm(Form):
    """Form which is used for register new member and also Log In function."""

    email = StringField('Email Address', validators=[
        validators.DataRequired(),
        validators.Email()
    ])
    password = PasswordField('Password', validators=[
        validators.DataRequired(),
        validators.Length(min=8)
    ])


class ConnectionForm(Form):
    """Form which is used to create/edit Database connection."""

    type = SelectField('Connection Type',
                       coerce=int,
                       choices=Constants.CONNECTION_TYPES_LIST)
    name = StringField('Name', validators=[
        validators.DataRequired()
    ])
    host = StringField('DB Host', validators=[
        validators.DataRequired()
    ])
    port = IntegerField('DB Port', validators=[
        validators.optional()
    ])
    user_name = StringField('Username', validators=[
        validators.DataRequired()
    ])
    password = PasswordField('Password')
    database = StringField('Database', validators=[
        validators.DataRequired()
    ])


class ScheduleForm(Form):
    """Used to create/edit job's schedule."""

    schedule_id = HiddenField(validators=[
        validators.Optional()
    ])
    schedule_type = SelectField('Schedule Type',
                                coerce=int,
                                choices=Constants.SCHEDULE_TYPES_LIST)
    next_run = StringField('Start On',
                           validators=[
                               validators.DataRequired()
                           ])
    is_active = BooleanField('Active')


class QueryJobForm(Form):
    """Used to create/edit data getting jobs."""

    name = StringField('Name',
                       render_kw={
                           'placeholder': 'Your job name'
                       },
                       validators=[
                           validators.DataRequired()
                       ])
    annotation = TextAreaField('Annotation',
                               render_kw={
                                   'placeholder': 'Job\'s annotation'
                               })
    connection_id = SelectField('Connection',
                                coerce=int)
    query_string = TextAreaField('Query',
                                 validators=[validators.DataRequired()]
                                 )
    query_time_out = IntegerField('Query Time Out',
                                  validators=[
                                      validators.DataRequired(),
                                      validators.NumberRange(min=0)
                                  ],
                                  default=config.get('DB_TIMEOUT', 0))
    emails = FieldList(StringField('Email',
                                   render_kw={
                                       'placeholder': 'report_to@viisix.space'
                                   },
                                   validators=[
                                       validators.Optional(),
                                       validators.Email()
                                   ]),
                       'Send Result To',
                       min_entries=1)
    schedules = FieldList(FormField(ScheduleForm),
                          'Job\'s schedules:')

    def populate_obj(self, obj):
        """
        Populate form to object.

        Since Form's default `populate_obj` function populate all
        the fields in this class, this function will do the same
        function except `emails` field.

        :param obj: Job Model object.
        """
        for name, field in iteritems(self._fields):
            if name not in ['query_time_out', 'emails', 'schedules']:
                field.populate_obj(obj, name)
