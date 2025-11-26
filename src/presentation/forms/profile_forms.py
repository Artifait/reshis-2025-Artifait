from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import Optional, Length, Regexp


class ProfileForm(FlaskForm):
    first_name = StringField('Имя', validators=[Optional(), Length(max=50)])
    last_name = StringField('Фамилия', validators=[Optional(), Length(max=50)])
    telegram_id = StringField(
        'Telegram ID',
        validators=[
            Optional(),
            Length(max=60),
            Regexp(r'^[0-9-]+$', message='Telegram ID должен содержать только цифры и знак "-"')
        ]
    )

    submit = SubmitField('Сохранить')
    delete_telegram = SubmitField('Удалить Telegram ID')