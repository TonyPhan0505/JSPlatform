from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import time

user_task = db.Table('user_task',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('task_id', db.Integer, db.ForeignKey('task.id'))
)

role_permission = db.Table('role_permission',
	db.Column('role_id', db.Integer, db.ForeignKey('role.id')),
	db.Column('permission_id', db.Integer, db.ForeignKey('permission.id'))
)

user_notification = db.Table('user_notification',
	db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('notification_id', db.Integer, db.ForeignKey('notification.id'))
)

class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String, unique = False)
	email = db.Column(db.String, unique = True)
	password_hash = db.Column(db.String, unique = False)
	performance_point = db.Column(db.Float)
	company_code = db.Column(db.String)
	host = db.Column(db.Boolean)
	approved = db.Column(db.Boolean)
	department_id = db.Column(db.Integer, db.ForeignKey("department.id"))
	tasks = db.relationship("Task", secondary=user_task, backref='users')
	notifications = db.relationship("Notification", secondary=user_notification, backref='users')
	role_id = db.Column(db.Integer, db.ForeignKey("role.id"))
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def has_permission(self, permission):
		role = Role.query.get(self.role_id)
		permission = Permission.query.filter_by(name = permission).first()
		if role and permission in role.permissions:
			return True
		return False
	
	def is_host(self):
		return self.host
	
	def set_as_host(self):
		self.host = True

	def set_as_participant(self):
		self.host = False

	def is_approved(self):
		return self.approved
	
	def set_as_approved(self):
		self.approved = True

	def set_as_pending(self):
		self.approved = False

class Company(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String, unique = False)
	ceo = db.Column(db.String, unique = False)
	company_code = db.Column(db.String, unique = True)
	procedures = db.relationship("Procedure", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")
	orders = db.relationship("Order", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")
	services = db.relationship("Service", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")  # records of services the company has done
	departments = db.relationship("Department", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")
	roles = db.relationship("Role", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")
	users = db.relationship("User", backref="company", lazy="dynamic", cascade="all, delete, delete-orphan")

	def get_host(self):
		for user in self.users:
			if user.is_host():
				return user

class Procedure(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	service = db.Column(db.String, unique = False)
	standard_tasks = db.relationship("StandardTask", backref="procedure", lazy="dynamic", cascade="all, delete, delete-orphan")
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

class Order(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	service = db.Column(db.String, unique = False)
	client_name = db.Column(db.String)
	completion_status = db.Column(db.Float)  # a rounded percentage value from 0.0 to 100.0
	time_created = db.Column(db.String)
	time_updated = db.Column(db.String)
	time_completed = db.Column(db.String)
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
	tasks = db.relationship("Task", backref="order", lazy="dynamic", cascade="all, delete, delete-orphan")

	def set_time_created(self):
		self.time_created = time.asctime()
	
	def set_time_updated(self):
		self.time_updated = time.asctime()

	def set_time_completed(self):
		self.time_completed = time.asctime()

# Services the company has provided
class Service(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String, unique = False)
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

# A Task object represents a step in an order
class Task(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String)
	departments = db.Column(db.String)  # name of departments that are responsible for this task
	roles = db.Column(db.String)
	description = db.Column(db.String)
	step_number = db.Column(db.Integer)
	status = db.Column(db.Integer) # 0 for incomplete, 1 for complete
	order_id = db.Column(db.Integer, db.ForeignKey("order.id"))
	files = db.relationship("File", backref="task", lazy="dynamic", cascade="all, delete, delete-orphan")
	
class StandardTask(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	title = db.Column(db.String)
	departments = db.Column(db.String)
	roles = db.Column(db.String)
	description = db.Column(db.String)
	step_number = db.Column(db.Integer)
	procedure_id = db.Column(db.Integer, db.ForeignKey("procedure.id"))

class Department(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String)
	performance_point = db.Column(db.Float)  # = number of tasks completed / number of tasks assigned, 1 decimal place, range from 0.0 to 100.0
	users = db.relationship("User", backref="department", lazy="dynamic")
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

class Role(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String)
	users = db.relationship("User", backref="role", lazy="dynamic")
	company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
	permissions = db.relationship("Permission", secondary=role_permission, backref='roles')

class Permission(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String, unique = True)

class File(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String)
	task_id = db.Column(db.Integer, db.ForeignKey("task.id"))

class Notification(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	time_created = db.Column(db.String)
	title = db.Column(db.String)
	message = db.Column(db.String)
	redirection = db.Column(db.String)