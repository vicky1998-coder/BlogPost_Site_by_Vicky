from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms import validators
from wtforms.fields.core import Label
from wtforms.validators import DataRequired, URL, Email, Length
from flask_ckeditor import CKEditorField


##WTForm
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# Registration form
class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = EmailField(label="Email", validators=[DataRequired(), Email(message="Invalid Email Format")])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=8,
                                                                                  message="Password should be at least 8 characters long.")])
    submit = SubmitField("SIGN ME UP!")


# Login Form
class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email(message="Invalid Email format")])
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="LET ME IN!")


# Comment Form
class CommentForm(FlaskForm):
    comment_box = CKEditorField(label="Comment", validators=[DataRequired()])
    submit = SubmitField("SUBMIT COMMENT")


# Contact Form
class ContactForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired(message="Please enter your name")], render_kw={"class": "form-contrl-lg"})
    email = EmailField(label="Email", validators=[DataRequired(), Email(message="Invalid email type")])
    phone = StringField(label="Phone Number")
    message = TextAreaField(label="Message", validators=[DataRequired()], render_kw={"style": 'height: 150px;'})
    submit = SubmitField(label="SEND", render_kw={"class": "btn btn-primary"})
