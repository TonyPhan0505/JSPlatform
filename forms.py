from flask_wtf import FlaskForm
import email_validator
from wtforms import StringField, SubmitField, PasswordField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, EqualTo

class CompanySignUpForm(FlaskForm):
	name = StringField("Company's Name", validators=[DataRequired()])
	ceo = StringField("CEO's/Director's Name", validators=[DataRequired()])
	company_code = StringField("Company's Login Code", validators=[DataRequired()])
	submit = SubmitField("Sign Up")

class UserSignUpForm(FlaskForm):
	name = StringField("Full Name", validators=[DataRequired()])
	email = StringField("Email", validators=[DataRequired(), Email()])
	password_one = PasswordField("Password", validators=[DataRequired()])
	password_two = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo('password_one')])
	company_code = PasswordField("Company's Code", validators=[DataRequired()])
	submit = SubmitField("Sign Up")

class UserLoginForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired(), Email()])
	password = PasswordField("Password", validators=[DataRequired()])
	submit = SubmitField("Login")

class CreateNewProcedureForm(FlaskForm):
	service = StringField("Name of Service", validators=[DataRequired()])
	submit = SubmitField("Create")

class CreateTaskForm(FlaskForm):
	title = StringField("Title", validators=[DataRequired()])
	departments = StringField("Departments", validators=[DataRequired()], render_kw={"placeholder": "use commas to separate departments"})
	roles = StringField("Roles", validators = [DataRequired()], render_kw={"placeholder": "use commas to separate roles"})
	description = TextAreaField("Description", validators=[DataRequired()])
	submit = SubmitField("Save")

class DepartmentRegistrationForm(FlaskForm):
	name = StringField("Department's Name", validators=[DataRequired()])
	submit = SubmitField("Save")

class RoleRegistrationForm(FlaskForm):
	name = StringField("Role's Name", validators=[DataRequired()])
	submit = SubmitField("Save")

class NewOrderCreationForm(FlaskForm):
	service = SelectField("Name of Service", choices=[], validators = [DataRequired()])
	client_name = StringField("Name of Client", validators=[DataRequired()])
	submit = SubmitField("Create")

class ChangePasswordForm(FlaskForm):
	current_password = PasswordField("Current Password", validators=[DataRequired()])
	password_one = PasswordField("New Password", validators=[DataRequired()])
	password_two = PasswordField("Confirm New Password", validators=[DataRequired(), EqualTo('password_one')])
	submit = SubmitField("Save")

class ChangeDepartmentAndRoleForm(FlaskForm):
	department = SelectField("Department", choices=[], validators = [DataRequired()])
	role = SelectField("Role", choices=[], validators = [DataRequired()])
	submit = SubmitField("Save")

class ActiveOrdersFiltersForm(FlaskForm):
	service = SelectField("Service", choices=[], validators = [])
	client_name = StringField("Client", validators=[])
	day = SelectField("Day Created", choices = [str(day) for day in range(1, 32)], validators=[])
	month = SelectField("Month Created", choices = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec'], validators=[])
	year = SelectField("Year Created", choices = [str(year) for year in range(2022, 2091)], validators = [])
	submit = SubmitField("Filter")

class CompletedOrdersFiltersForm(FlaskForm):
	service = SelectField("Service", choices=[], validators = [])
	client_name = StringField("Client", validators=[])
	day = SelectField("Day Completed", choices = [str(day) for day in range(1, 32)], validators=[])
	month = SelectField("Month Completed", choices = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], validators=[])
	year = SelectField("Year Completed", choices = [str(year) for year in range(2022, 2091)], validators = [])
	submit = SubmitField("Filter")

class PasswordRecoveryRequestForm(FlaskForm):
	email = StringField("Email", validators=[DataRequired()])
	submit = SubmitField("Continue")

class UploadFileForm(FlaskForm):
	file = FileField("Browse", validators=[DataRequired()])
	submit = SubmitField("Submit")

class ChangeCompanyCodeForm(FlaskForm):
	company_code = StringField("Company's Code", validators=[DataRequired()])
	submit = SubmitField("Save")