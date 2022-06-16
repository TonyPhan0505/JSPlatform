from app import app, db, mail
from flask import request, render_template, redirect, url_for, current_app, send_from_directory
from models import *
from forms import *
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
from helper_functions import *
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import os
import time

invalid_characters = "`~!@#$%^&*()-_+=[{]}\|;:'" + '"' + ",<.>/?"

permissions = ["Create Orders",
		"Delete Orders",
		"Insert Tasks",
		"Edit Tasks",
		"Delete Tasks",
		"Check Tasks As Completed",
		"Add and Remove Participants",
		"Create Procedures",
		"Delete Procedures",
		"Create Standard Tasks",
		"Delete Standard Tasks",
		"Edit Standard Tasks"]

@app.route('/')
def landing():
	if not Permission.query.all():
		for name in permissions:
			permission = Permission(name = name)
			db.session.add(permission)
			try:
				db.session.commit()
			except: 
				db.session.rollback()
	return render_template("landing.html")

@app.route('/register_company', methods = ['GET', 'POST'])
def register_company():
	form = CompanySignUpForm(csrf_enabled = False)
	if form.validate_on_submit():
		name = form.name.data
		ceo = form.ceo.data
		company_code = form.company_code.data
		if [c for c in name if c in invalid_characters] or [c for c in ceo if c in invalid_characters] or [c for c in company_code if c in invalid_characters]:
			return render_template("error_message.html", error_message = "YOUR INPUT CONTAINS INVALID CHARACTER(S)", endpoint = "register_company")
		if len(company_code) < 5:
			return render_template("error_message.html", error_message = "YOUR COMPANY'S CODE HAS TO BE LONGER THAN 5 CHARACTERS", endpoint = "register_company")
		if " " in company_code:
			return render_template("error_message.html", error_message = "YOUR COMPANY'S CODE CANNOT CONTAIN SPACES", endpoint = "register_company")
		company = Company(name = name, ceo = ceo, company_code = company_code)
		db.session.add(company)
		try:
			db.session.commit()
			return redirect(url_for('register_user'))
		except:
			db.session.rollback()
	return render_template("register_company.html", form = form)

@app.route('/register_departments', methods = ['GET', 'POST'])
@login_required
def register_departments():
	form = DepartmentRegistrationForm(csrf_enabled = False)
	if form.validate_on_submit():
		company = Company.query.get(current_user.company_id)
		if company:
			name = form.name.data
			if is_not_a_registered_department(name, company):
				if [c for c in name if c in invalid_characters]:
					return render_template("error_message.html", error_message = "THE DEPARTMENT'S NAME CONTAINS INVALID CHARACTERS", endpoint = "register_departments")
				department = Department(name = name, performance_point = 0.0, company_id = company.id)
				db.session.add(department)
				try:
					db.session.commit()
					return render_template("success_message.html", success_message = "SUCCESSFULLY SAVED", endpoint = "register_departments")
				except:
					db.session.rollback()
			else:
				return render_template("error_message.html", error_message = "ALREADY REGISTERED", endpoint = "register_departments")
		else:
			return render_template("error_message.html", error_message = "INCORRECT COMPANY'S CODE", endpoint = "register_departments")
	return render_template("register_departments.html", form = form)

@app.route('/register_roles', methods = ['GET', 'POST'])
@login_required
def register_roles():
	form = RoleRegistrationForm(csrf_enabled = False)
	if form.validate_on_submit():
		company = Company.query.get(current_user.company_id)
		if company:
			name = form.name.data
			if is_not_a_registered_role(name, company):
				if [c for c in name if c in invalid_characters]:
					return render_template("error_message.html", error_message = "THE ROLE'S NAME CONTAINS INVALID CHARACTERS", endpoint = "register_roles")
				role = Role(name = name, company_id = company.id)
				db.session.add(role)
				try:
					db.session.commit()
					return render_template("success_message.html", success_message = "SUCCESSFULLY SAVED", endpoint = "register_roles")
				except:
					db.session.rollback()
			else:
				return render_template("error_message.html", error_message = "ALREADY REGISTERED", endpoint = "register_roles")
		else:
			return render_template("error_message.html", error_message = "INCORRECT COMPANY'S CODE", endpoint = "register_roles")
	return render_template("register_roles.html", form = form)

@app.route("/user_registration_confirmation/<string:company_name>/<string:ceo>/<string:receiver_email>/<string:password>")
def user_registration_confirmation(company_name, ceo, receiver_email, password):
	msg = Message(f'Welcome to {company_name}', sender = ('JS Platform', 'juststartplatform@aol.com'), recipients = [receiver_email])
	msg.body = f"You have registered an account on JustStart with the email: {receiver_email}. Your password is: {password}. Your company is: {company_name}, whose CEO/Director is: {ceo}.\n\nAfter logging in, you should head right to registering your department and role in Account Info. If you don't see your department or role, tell your host to add it. If you are the host, head to Settings to add departments and roles."
	mail.send(msg)
	return redirect(url_for('login'))

@app.route('/register_user', methods = ['GET', 'POST'])
def register_user():
	form = UserSignUpForm(csrf_enabled = False)
	if form.validate_on_submit():
		company_code = form.company_code.data
		company = Company.query.filter_by(company_code = company_code).first()
		if company:
			if not registered_with_departments(company) and company.users.count() > 0:
				return render_template("error_message.html", error_message = "YOUR COMPANY'S HOST HASN'T REGISTERED ANY DEPARTMENTS YET", endpoint = "register_user")
			elif not registered_with_roles(company) and company.users.count() > 0:
				return render_template("error_message.html", error_message = "YOUR COMPANY'S HOST HASN'T REGISTERED ANY ROLES YET", endpoint = "register_user")
			else:
				name = form.name.data
				if [c for c in name if c in invalid_characters]:
					return render_template("error_message.html", error_message = "YOUR NAME CONTAINS INVALID CHARACTERS", endpoint = "register_user")
				email = form.email.data
				user = User(name = name, email = email, performance_point = 0.0, company_code = company_code, company_id = company.id)
				password = form.password_one.data
				user.set_password(password)
				if company.users.count() == 0:
					user.set_as_host()
					user.set_as_approved()
				else:
					user.set_as_participant()
					user.set_as_pending()
				db.session.add(user)
				try:
					db.session.commit()
					company_name = company.name
					ceo = company.ceo
					return redirect(url_for('user_registration_confirmation', company_name = company_name, ceo = ceo, receiver_email = email, password = password))
				except:
					db.session.rollback()
	return render_template("register_user.html", form = form)

@app.route("/password_recovery_message/<string:receiver_email>/<string:password>")
def password_recovery_message(receiver_email, password):
	msg = Message('This Is Your Temporary Password', sender = ('JS Platform', 'juststartplatform@aol.com'), recipients = [receiver_email])
	msg.body = "Your temporary password is: " + password + ". You can change this password after logging in."
	mail.send(msg)
	return render_template("success_message.html", success_message = "AN EMAIL HAS JUST BEEN SENT TO YOU", endpoint = 'login')

@app.route('/recover_password_request', methods=['GET', 'POST'])
def recover_password_request():
	form = PasswordRecoveryRequestForm(csrf_enabled = False)
	if form.validate_on_submit():
		email = form.email.data
		user = User.query.filter_by(email = email).first()
		if user:
			temporary_password = generate_temporary_password()
			user.set_password(temporary_password)
			try:
				db.session.commit()
				return redirect(url_for('password_recovery_message', receiver_email = email, password = temporary_password))
			except:
				db.session.rollback()
		else:
			return render_template("error_message.html", error_message = "USER NOT FOUND", endpoint = 'recover_password_request')
	return render_template("recover_password.html", form = form)

@app.route('/login', methods = ['GET', 'POST'])
def login():
	form = UserLoginForm(csrf_enabled = False)
	if form.validate_on_submit():
		email = form.email.data
		password = form.password.data
		user = User.query.filter_by(email = email).first()
		if user and user.check_password(password):
			if not user.is_approved():
				return render_template("error_message.html", error_message = "YOUR HOST HASN'T APPROVED YOUR REGISTRATION", endpoint = 'login')
			else: 
				login_user(user)
				return redirect(url_for('dashboard'))
		else:
			return render_template("error_message.html", error_message = "INVALID EMAIL OR PASSWORD", endpoint = 'login')
	return render_template("login.html", form = form)

@app.route("/dashboard", methods = ['GET', 'POST'])
@login_required
def dashboard():
	active_orders = get_active_orders(current_user.company_id)[::-1]
	completed_orders = get_completed_orders(current_user.company_id)[::-1]
	return render_template("dashboard.html", active_orders = active_orders, completed_orders = completed_orders, current_user = current_user)

@app.route("/active_orders_filters", methods = ['GET', 'POST'])
@login_required
def active_orders_filters():
	form = ActiveOrdersFiltersForm(csrf_enabled=False)
	form.service.choices = get_services(current_user.company_id)
	if form.validate_on_submit():
		service_name = form.service.data
		client_name = form.client_name.data
		if not client_name: client_name = 'All'
		day = form.day.data
		month = form.month.data
		year = form.year.data
		return redirect(url_for('filtered_active_orders', service_name = service_name, client_name = client_name, day = day, month = month, year = year))
	return render_template("active_orders_filters.html", form = form)

@app.route("/filtered_active_orders/<string:service_name>/<string:client_name>/<string:day>/<string:month>/<string:year>", methods=['GET', 'POST'])
@login_required
def filtered_active_orders(service_name, client_name, day, month, year):
	result_1 = get_service_filtered_active_orders(current_user.company_id, service_name)
	result_2 = get_client_filtered_active_orders(current_user.company_id, client_name)
	result_3 = get_time_created_filtered_active_orders(current_user.company_id, day, month, year)
	filtered_orders = set(result_1) & set(result_2) & set(result_3)
	if not filtered_orders:
		return render_template("error_message.html", error_message = "NO RESULTS FOUND", endpoint = 'active_orders_filters')
	return render_template("filtered_active_orders.html", filtered_orders = filtered_orders)

@app.route("/completed_orders_filters", methods = ['GET', 'POST'])
@login_required
def completed_orders_filters():
	form = CompletedOrdersFiltersForm(csrf_enabled=False)
	form.service.choices = get_services(current_user.company_id)
	if form.validate_on_submit():
		service_name = form.service.data
		client_name = form.client_name.data
		day = form.day.data
		month = form.month.data
		year = form.year.data
		return redirect(url_for('filtered_completed_orders', service_name = service_name, client_name = client_name, day = day, month = month, year = year))
	return render_template("completed_orders_filters.html", form = form)

@app.route("/filtered_completed_orders/<string:service_name>/<string:client_name>/<string:day>/<string:month>/<string:year>", methods=['GET', 'POST'])
@login_required
def filtered_completed_orders(service_name, client_name, day, month, year):
	result_1 = get_service_filtered_completed_orders(current_user.company_id, service_name)
	result_2 = get_client_filtered_completed_orders(current_user.company_id, client_name)
	result_3 = get_time_completed_filtered_completed_orders(current_user.company_id, day, month, year)
	filtered_orders = set(result_1) & set(result_2) & set(result_3)
	if not filtered_orders:
		return render_template("error_message.html", error_message = "NO RESULTS FOUND", endpoint = 'completed_orders_filters')
	return render_template("filtered_completed_orders.html", filtered_orders = filtered_orders)

@app.route("/create_new_order", methods = ['GET', 'POST'])
@login_required
def create_new_order():
	if current_user.has_permission("Create Orders"):
		form = NewOrderCreationForm(csrf_enabled = False)
		all_services = get_services(current_user.company_id)
		if all_services:
			form.service.choices = all_services
			if form.validate_on_submit():
				service_name = form.service.data
				client_name = form.client_name.data
				order = Order(service = service_name, client_name = client_name, completion_status = 0.0, company_id = current_user.company_id)
				order.set_time_created()
				order.set_time_updated()
				all_tasks = get_standard_tasks_for_order(service_name, current_user.company_id)
				order.tasks.extend(all_tasks)
				for task in all_tasks:
					people_in_charge = get_people_in_charge_for_task(task, current_user)
					for person in people_in_charge:
						add_participant_to_task(task.id, person.id, current_user)
				db.session.add(order)
				try:
					db.session.commit()
					first_task = all_tasks[0]
					people_in_charge_of_first_task = get_people_in_charge_for_task(first_task, current_user)
					notify_people_of_first_task(first_task, people_in_charge_of_first_task, current_user)
					return render_template("success_message.html", success_message = "SUCCESSFULLY CREATED ORDER", endpoint = 'create_new_order')
				except:
					db.session.rollback()
		else:
			return render_template("error_message.html", error_message = "YOUR COMPANY NEEDS TO CREATE THE PROCEDURES FIRST", endpoint = 'dashboard')
		return render_template("create_new_order.html", form = form)
	else:
		return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = 'dashboard')

@app.route("/procedures", methods = ['GET', 'POST'])
@login_required
def procedures():
	procedures = get_all_procedures(current_user.company_id)
	return render_template("procedures.html", procedures = procedures, current_user = current_user)

@app.route("/statistics", methods = ['GET', 'POST'])
@login_required
def statistics():
	employees_ranking_board = get_employees_ranking_board(current_user.company_id)
	departments_ranking_board = get_departments_ranking_board(current_user.company_id)
	proportions_for_services = get_proportions_for_services(current_user.company_id)
	number_of_active_orders = get_number_of_active_orders(current_user.company_id)
	number_of_completed_orders = get_number_of_completed_orders(current_user.company_id)
	return render_template("statistics.html",
	employees_ranking_board = employees_ranking_board,
	departments_ranking_board = departments_ranking_board,
	proportions_for_services = proportions_for_services,
	number_of_active_orders = number_of_active_orders,
	number_of_completed_orders = number_of_completed_orders
	)

@app.route("/manage_procedure/<string:service_name>", methods = ['GET', 'POST'])
@login_required
def manage_procedure(service_name):
	if service_name == 'new':
		if current_user.has_permission("Create Procedures"):
			form = CreateNewProcedureForm(csrf_enabled = False)
		else:
			return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")
	else:
		if current_user.has_permission("Create Standard Tasks"):
			form = CreateTaskForm(csrf_enabled = False)
		else:
			return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")
	if form.validate_on_submit():
		if service_name == 'new':
			# add a new procedure to the database
			service_name = form.service.data
			if not is_a_registered_service(service_name, current_user.company_id):
				procedure = Procedure(service = service_name, company_id = current_user.company_id)
				service = Service(name = service_name, company_id = current_user.company_id)
				db.session.add(procedure)
				db.session.add(service)
				try:
					db.session.commit()
					return redirect(url_for('manage_procedure', service_name = service_name))
				except:
					db.session.rollback()
			else:
				return render_template("error_message.html", error_message = "THIS PROCEDURE WAS ALREADY CREATED", endpoint = "manage_procedure", service_name = "new")

		else:
			# add a standard task to the procedure
			departments = form.departments.data
			procedure = Procedure.query.filter_by(service = service_name, company_id = current_user.company_id).first()
			roles = form.roles.data
			if are_registered_departments(departments) and are_registered_roles(roles):
				standard_task = StandardTask(title = form.title.data,
				departments = departments,
				roles = roles,
				description = form.description.data,
				step_number = procedure.standard_tasks.count() + 1,
				procedure_id = procedure.id)
				db.session.add(standard_task)
				try:
					db.session.commit()
				except:
					db.session.rollback()
				return redirect(url_for('manage_procedure', service_name = service_name))
			else:
				return render_template("error_message.html", error_message = "ONE OR MORE OF THE DEPARTMENTS/ROLES IS NOT REGISTERED", endpoint = "manage_procedure", service_name = service_name)
	if service_name != "new":
		standard_tasks = get_standard_tasks(service_name, current_user.company_id)
	else: 
		standard_tasks = []
	return render_template("manage_procedure.html", form = form, service_name = service_name, standard_tasks = standard_tasks, current_user = current_user)

@app.route("/manage_standard_task/<string:service_name>/<int:standard_task_id>/<string:instruction>", methods = ['GET', 'POST'])
@login_required
def manage_standard_task(service_name, standard_task_id, instruction):
	standard_task = StandardTask.query.get(standard_task_id)
	if instruction == 'edit':
		if current_user.has_permission("Edit Standard Tasks"):
			form = CreateTaskForm(csrf_enabled = False)
			if form.validate_on_submit():
				standard_task.title = form.title.data
				standard_task.departments = form.departments.data
				standard_task.roles = form.roles.data
				standard_task.description = form.description.data
				try: 
					db.session.commit()
					return redirect(url_for('manage_procedure', service_name = service_name))
				except:
					db.session.rollback()
			form.title.data = standard_task.title
			form.departments.data = standard_task.departments
			form.roles.data = standard_task.roles
			form.description.data = standard_task.description
			return render_template("edit_task.html", form = form, back_endpoint = 'manage_procedure', service_name = service_name)
		else:
			return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")
	else:
		return redirect(url_for('delete_standard_task', service_name = service_name, standard_task_id = standard_task_id, decision = 'PENDING'))

@app.route("/delete_standard_task/<string:service_name>/<int:standard_task_id>/<string:decision>", methods=['GET', 'POST'])
@login_required
def delete_standard_task(service_name, standard_task_id, decision):
	if decision == 'PENDING':
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS TASK IN THIS PROCEDURE?", yes_endpoint = 'delete_standard_task', no_endpoint = 'manage_procedure', standard_task_id = standard_task_id, service_name = service_name)
	else:
		standard_task = StandardTask.query.get(standard_task_id)
		db.session.delete(standard_task)
		try:
			db.session.commit()
			reset_step_number_for_tasks_in_procedure_after_deletion(service_name, current_user.company_id)
		except:
			db.session.rollback()
	return redirect(url_for('manage_procedure', service_name = service_name))

@app.route("/manage_order/<int:order_id>", methods=['GET', 'POST'])
@login_required
def manage_order(order_id):
	try:
		order = Order.query.get(order_id)
		tasks = get_tasks_in_order(order)
		return render_template("manage_order.html", order = order, tasks = tasks, current_user = current_user)
	except:
		return render_template("error_message.html", error_message = "THIS ORDER NO LONGER EXISTS", endpoint = "dashboard")

@app.template_global()
def get_files_in_task(task_id):
	files = [file.name for file in File.query.filter(File.task_id == task_id).all()]
	return files

@app.route("/delete_order/<int:order_id>/<string:decision>", methods=['GET', 'POST'])
@login_required
def delete_order(order_id, decision):
	if decision == 'PENDING':
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS ORDER?", yes_endpoint = 'delete_order', no_endpoint = 'manage_order', order_id = order_id)
	else:
		order = Order.query.get(order_id)
		order_name = order.service
		client_name = order.client_name
		company_name = Company.query.get(order.company_id).name
		time_created = order.time_created
		tasks = order.tasks
		associated_people = []
		for task in tasks:
			files = [file.name for file in File.query.filter(File.task_id == task.id).all()]
			for file in files:
				os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
			people = task.users
			associated_people.extend(people)
		db.session.delete(order)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		content = f"The order titled {order_name}, created on {time_created}, for the client called {client_name} has been deleted by {current_user.name} ({current_user.email}) from the department {Department.query.get(current_user.department_id).name}."
		notification = Notification(time_created = time.asctime(), title = "Order Deleted", message = content)
		db.session.add(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		
		for user in associated_people:
			user.notifications.append(notification)
			try:
				db.session.commit()
			except:
				db.session.rollback()
			receiver_email = user.email
			msg = Message(f'Order Deleted', sender = (f'{company_name}', 'juststartplatform@aol.com'), recipients = [receiver_email])
			msg.body = content + '\n\nGo to Account Info on JS Platform for more information.'
			mail.send(msg)
	return redirect(url_for('dashboard'))

@app.route("/traverse_order/<int:order_id>", methods = ['GET', 'POST'])
@login_required
def traverse_order(order_id):
	order = Order.query.get(order_id)
	order_completion_status = order.completion_status
	if order_completion_status < 100:
		incomplete_tasks = get_incomplete_tasks_in_order(order)
		current_task = incomplete_tasks[0]
		files = [file.name for file in File.query.filter(File.task_id == current_task.id).all()]
		return redirect(url_for('view_task_in_order', order_id = order_id, task_id = current_task.id))
	else:
		return redirect(url_for('manage_order', order_id = order_id))

@app.route("/view_task_in_order/<int:order_id>/<int:task_id>", methods = ['GET', 'POST'])
@login_required
def view_task_in_order(order_id, task_id):
	current_task = Task.query.get(task_id)
	files = [file.name for file in File.query.filter(File.task_id == current_task.id).all()]
	participants = ", ".join([user.name for user in current_task.users])
	if not participants:
		participants = "Not assigned"
	form = UploadFileForm(csrf_enabled = False)
	if form.validate_on_submit():
		file = form.file.data
		filename = secure_filename(file.filename)
		if filename in files:
			return render_template("error_message.html", error_message = "THIS FILE ALREADY EXISTED. PLEASE CHANGE YOUR FILENAME OR REMOVE THE PREVIOUS ONE.", endpoint = "view_task_in_order", order_id = order_id, task_id = task_id)
		elif '.' not in filename or filename.rsplit('.', 1)[1].lower() not in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'docx'}:
			return render_template("error_message.html", error_message = "THIS FILE EXTENSION IS NOT SUPPORTED.", endpoint = "view_task_in_order", order_id = order_id, task_id = task_id)
		else:
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			document = File(name = filename, task_id = current_task.id)
			db.session.add(document)
			try:
				db.session.commit()
				return redirect(url_for('view_task_in_order', order_id = order_id, task_id = task_id))
			except:
				db.session.rollback()
	return render_template("task_in_order.html", order_id = order_id, current_task = current_task, participants = participants, current_user = current_user, form = form, files = files)

@app.route("/download_file/<path:filename>", methods = ['GET', 'POST'])
@login_required
def download_file(filename):
	uploads = app.config['UPLOAD_FOLDER']
	return send_from_directory(uploads, filename)

@app.route("/delete_file/<int:order_id>/<int:task_id>/<path:filename>/<string:decision>", methods = ['GET', 'POST'])
@login_required
def delete_file(order_id, task_id, filename, decision):
	if decision == 'PENDING':
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO REMOVE THIS FILE?", yes_endpoint = 'delete_file', no_endpoint = 'traverse_order', order_id = order_id, task_id = task_id, filename = filename)
	else:
		try:
			os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			file = File.query.filter_by(name = filename, task_id = task_id).first()
			db.session.delete(file)
			try:
				db.session.commit()
			except:
				db.session.rollback()
		except:
			return redirect(url_for('traverse_order', order_id = order_id))
	return redirect(url_for('traverse_order', order_id = order_id))

@app.route("/check_task/<int:order_id>/<int:task_id>", methods = ['GET'])
@login_required
def check_task(order_id, task_id):
	reset_updated_time_for_order(order_id)
	set_task_as_completed(task_id)
	reset_completion_status_for_order(order_id)
	reset_performance_point_for_departments_in_task(task_id, current_user.company_id)
	reset_performance_point_for_user(current_user)
	order = Order.query.get(order_id)
	order_completion_status = order.completion_status
	if order_completion_status < 100:
		next_task = get_incomplete_tasks_in_order(order)[0]
		responsible_people = next_task.users
		if responsible_people:
			notify_people_on_next_task(next_task, responsible_people)
		return redirect(url_for('traverse_order', order_id = order_id))
	else:
		return redirect(url_for('manage_order', order_id = order_id))

@app.route("/redo_task/<int:order_id>/<int:task_id>", methods = ['GET'])
@login_required
def redo_task(order_id, task_id):
	task = Task.query.get(task_id)
	task.status = 0
	try:
		db.session.commit()
	except:
		db.session.rollback()
	reset_completion_status_for_order(order_id)
	
	task_title = task.title
	step_number = task.step_number
	order_id = task.order_id
	order = Order.query.get(order_id)
	service_name = order.service
	client_name = order.client_name
	order_creation_time = order.time_created
	notification_creation_time = time.asctime()
	company_name = Company.query.get(order.company_id).name
	author = current_user.name
	author_email = current_user.email
	author_department = Department.query.get(current_user.department_id).name
	content = f"{author} ({author_email}) from the {author_department} department has demanded the task titled '{task_title}' with step number {step_number} in the order titled '{service_name}' for the client called '{client_name}' created on {order_creation_time} to be redone. You were one of the employees assigned to this task. Go back and redo the task now!"
	notification = Notification(time_created = notification_creation_time, title = "Redo Your Task", message = content, redirection = f"/manage_order/{order_id}")
	db.session.add(notification)
	try:
		db.session.commit()
	except:
		db.session.rollback()
	for user in task.users:
		user.notifications.append(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		receiver_email = user.email
		msg = Message(f'Redo Your Task', sender = (f'{company_name}', 'juststartplatform@aol.com'), recipients = [receiver_email])
		msg.body = content + '\n\nGo to Account Info on JS Platform for more information.'
		mail.send(msg)
	
	return redirect(url_for('view_task_in_order', order_id = order_id, task_id = task_id))

@app.route("/manage_task_in_order/<string:previous>/<int:order_id>/<int:task_id>/<string:instruction>", methods=['GET', 'POST'])
@login_required
def manage_task_in_order(previous, order_id, task_id, instruction):
	task = Task.query.get(task_id)
	if instruction == 'edit':
		if current_user.has_permission("Edit Tasks"):
			form = CreateTaskForm(csrf_enabled = False)
			if form.validate_on_submit():
				task.title = form.title.data
				task.departments = form.departments.data
				task.roles = form.roles.data
				task.description = form.description.data
				try: 
					db.session.commit()
					reset_updated_time_for_order(order_id)
					return redirect(url_for('traverse_order', order_id = order_id))
				except:
					db.session.rollback()
			form.title.data = task.title
			form.departments.data = task.departments
			form.roles.data = task.roles
			form.description.data = task.description
			return render_template("edit_task.html", form = form, back_endpoint = 'traverse_order', order_id = order_id)
		else:
			return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")
	elif instruction == 'delete':
		return redirect(url_for('delete_task_in_order', previous = previous, order_id = order_id, task_id = task_id, decision = 'PENDING'))
	else:
		return redirect(url_for('insert_new_task_into_order', order_id = order_id, current_step_number = task.step_number))

@app.route("/insert_new_task_into_order/<int:order_id>/<int:current_step_number>", methods=['GET', 'POST'])
@login_required
def insert_new_task_into_order(order_id, current_step_number):
	if current_user.has_permission("Insert Tasks"):
		form = CreateTaskForm(csrf_enabled = False)
		if form.validate_on_submit():
			departments = form.departments.data
			roles = form.roles.data
			if are_registered_departments(departments) and are_registered_roles(roles):
				temporary_step_number_for_new_task = Order.query.get(order_id).tasks.count() + 1
				new_task = Task(title = form.title.data, departments = departments, roles = roles, description = form.description.data, step_number = temporary_step_number_for_new_task, status = 0, order_id = order_id)
				db.session.add(new_task)
				try:
					db.session.commit()
					reset_updated_time_for_order(order_id)
					reset_completion_status_for_order(order_id)
					reset_step_number_for_tasks_in_order_after_insertion(order_id, current_step_number, new_task)
					return redirect(url_for('traverse_order', order_id = order_id))
				except:
					db.session.rollback()
			else:
				return render_template("error_message.html", error_message = "UNREGISTERED DEPARTMENT(S) DETECTED", endpoint = "insert_new_task_into_order", order_id = order_id, current_step_number = current_step_number)
		return render_template("insert_new_task_into_order.html", form = form, order_id = order_id)
	else:
		return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")

@app.route("/delete_task_in_order/<string:previous>/<int:order_id>/<int:task_id>/<string:decision>", methods=['GET', 'POST'])
@login_required
def delete_task_in_order(previous, order_id, task_id, decision):
	if decision == 'PENDING':
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS TASK IN THIS ORDER?", yes_endpoint = 'delete_task_in_order', no_endpoint = 'traverse_order', previous = previous, order_id = order_id, task_id = task_id)
	else:
		task = Task.query.get(task_id)
		files = [file.name for file in File.query.filter(File.task_id == task.id).all()]
		for file in files:
			os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
		db.session.delete(task)
		try:
			db.session.commit()
			reset_updated_time_for_order(order_id)
			reset_step_number_for_tasks_in_order_after_deletion(order_id)
			reset_completion_status_for_order(order_id)
		except:
			db.session.rollback()
	return redirect(url_for(previous, order_id = order_id))

@app.route("/manage_people_on_task/<int:task_id>/<string:previous>", methods = ['GET', 'POST'])
@login_required
def manage_people_on_task(task_id, previous):
	if current_user.has_permission("Add and Remove Participants"):
		task = Task.query.get(task_id)
		relevant_people = get_relevant_people_for_task(task, current_user)
		return render_template("manage_people_on_task.html", task = task, relevant_people = relevant_people, previous = previous)
	else:
		return render_template("error_message.html", error_message = "YOU DO NOT HAVE PERMISSION TO ACCESS THIS PAGE", endpoint = "dashboard")

@app.route("/add_person_to_task/<string:previous>/<int:task_id>/<int:user_id>", methods=['GET', 'POST'])
@login_required
def add_person_to_task(previous, task_id, user_id):
	add_participant_to_task(task_id, user_id, current_user)
	return redirect(url_for('manage_people_on_task', task_id = task_id, previous = previous))

@app.route("/remove_person_from_task/<string:previous>/<int:task_id>/<int:user_id>", methods=['GET', 'POST'])
@login_required
def remove_person_from_task(previous, task_id, user_id):
	task = Task.query.get(task_id)
	user = User.query.get(user_id)
	task.users.remove(user)
	try:
		db.session.commit()
		reset_updated_time_for_order(task.order_id)
	except:
		db.session.rollback()
	return redirect(url_for('manage_people_on_task', task_id = task_id, previous = previous))

@app.route("/delete_procedure/<int:procedure_id>/<string:decision>", methods = ['GET', 'POST'])
@login_required
def delete_procedure(procedure_id, decision):
	if decision == "PENDING":
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS PROCEDURE?", yes_endpoint = 'delete_procedure', no_endpoint = 'procedures', procedure_id = procedure_id)
	else:
		procedure = Procedure.query.get(procedure_id)
		service = Service.query.filter_by(name = procedure.service, company_id = current_user.company_id).first()
		db.session.delete(procedure)
		db.session.delete(service)
		try: 
			db.session.commit()
		except:
			db.session.rollback()
	return redirect(url_for('procedures'))

@app.route("/manage_user", methods=['GET', 'POST'])
@login_required
def manage_user():
	number_of_tasks_completed = get_number_of_completed_tasks_for_user(current_user)
	number_of_tasks = get_number_of_tasks_for_user(current_user)
	performance_point = calculate_performance_point_for_user(current_user)
	user_name = current_user.name
	email = current_user.email
	company = Company.query.get(current_user.company_id)
	company_name = company.name
	company_code = company.company_code
	ceo = company.ceo
	host = company.get_host()
	host_name = host.name
	host_email = host.email
	department_id = current_user.department_id
	if department_id:
		department = Department.query.get(department_id).name
		number_of_tasks_for_department = get_number_of_tasks_for_department(department, current_user.company_id)
		number_of_completed_tasks_for_department = get_number_of_completed_tasks_for_department(department, current_user.company_id)
	else:
		department = "Unregistered"
		number_of_tasks_for_department = 0
		number_of_completed_tasks_for_department = 0
	role_id = current_user.role_id
	if role_id:
		role = Role.query.get(current_user.role_id).name
	else:
		role = "Unregistered"
	notifications = current_user.notifications[::-1]
	return render_template("manage_user.html",
	number_of_tasks_completed = number_of_tasks_completed,
	number_of_tasks = number_of_tasks,
	performance_point = performance_point,
	user_name = user_name,
	email = email,
	company_name = company_name,
	company_code = company_code,
	ceo = ceo,
	department = department,
	role = role,
	number_of_tasks_for_department = number_of_tasks_for_department,
	number_of_completed_tasks_for_department = number_of_completed_tasks_for_department,
	host_name = host_name,
	host_email = host_email,
	notifications = notifications
	)

@app.route("/delete_notification/<int:notification_id>")
@login_required
def delete_notification(notification_id):
	notification = Notification.query.get(notification_id)
	db.session.delete(notification)
	try:
		db.session.commit()
	except:
		db.session.rollback()
	return redirect(url_for('manage_user'))

@app.route("/password_change_confirmation/<string:password>")
@login_required
def password_change_confirmation(password):
	msg = Message('Your Password Has Been Changed', sender = ('JS Platform', 'juststartplatform@aol.com'), recipients = [current_user.email])
	msg.body = "Your password has just been changed to: " + password
	mail.send(msg)
	return render_template("success_message.html", success_message = "A CONFIRMATION EMAIL HAS JUST BEEN SENT TO YOU", endpoint = "manage_user")

@app.route("/change_password", methods=['GET', 'POST'])
@login_required
def change_password():
	form = ChangePasswordForm(csrf_enabled = False)
	if form.validate_on_submit():
		if current_user.check_password(form.current_password.data):
			new_password = form.password_one.data
			current_user.set_password(new_password)
			try:
				db.session.commit()
				return redirect(url_for('password_change_confirmation', password = new_password))
			except:
				db.session.rollback()
		else:
			return render_template("error_message.html", error_message = "INCORRECT PASSWORD", endpoint = "change_password")
	return render_template("change_password.html", form = form)

@app.route("/change_department_and_role", methods=['GET', 'POST'])
@login_required
def change_department_and_role():
	form = ChangeDepartmentAndRoleForm(csrf_enabled = False)
	form.department.choices = get_departments(current_user.company_id)
	form.role.choices = get_roles(current_user.company_id)
	if form.validate_on_submit():
		department_name = form.department.data
		department_id = Department.query.filter_by(name = department_name, company_id = current_user.company_id).first().id
		current_user.department_id = department_id
		role_name = form.role.data
		role_id = Role.query.filter_by(name = role_name, company_id = current_user.company_id).first().id
		current_user.role_id = role_id
		try:
			db.session.commit()
			return render_template("success_message.html", success_message = "YOUR DEPARTMENT AND ROLE HAVE BEEN CHANGED", endpoint = "manage_user")
		except:
			db.session.rollback()
	return render_template("change_department_and_role.html", form = form)

@login_required
@app.route("/platform_settings", methods = ['GET', 'POST'])
def platform_settings():
	if not Department.query.filter(Department.company_id == current_user.company_id).all():
		return redirect(url_for('register_departments'))
	if not Role.query.filter(Role.company_id == current_user.company_id).all():
		return redirect(url_for('register_roles'))
	roles = Role.query.filter(Role.company_id == current_user.company_id).all()
	departments = Department.query.filter(Department.company_id == current_user.company_id).all()
	employees = sorted([user for user in Company.query.get(current_user.company_id).users if user.is_approved()], key = lambda user: user.email[0])
	pending_employees = [user for user in Company.query.get(current_user.company_id).users if not user.is_approved()][::-1]
	return render_template("platform_settings.html", roles = roles, permissions = permissions, departments = departments, employees = employees, pending_employees = pending_employees)

@app.route("/empower/<int:employee_id>", methods = ['GET', 'POST'])
@login_required
def empower(employee_id):
	employee = User.query.get(employee_id)
	company = Company.query.get(employee.company_id)
	current_host = company.get_host()
	current_host.set_as_participant()
	employee.set_as_host()
	try:
		db.session.commit()
	except:
		db.session.rollback()
	return redirect(url_for('dashboard'))

@app.route("/approve/<int:employee_id>", methods = ['GET', 'POST'])
@login_required
def approve(employee_id):
	employee = User.query.get(employee_id)
	employee.set_as_approved()
	try:
		db.session.commit()
	except:
		db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/remove_employee/<int:employee_id>/<string:decision>", methods = ['GET', 'POST'])
@login_required
def remove_employee(employee_id, decision):
	if decision == "PENDING":
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO REMOVE THIS EMPLOYEE?", yes_endpoint = 'remove_employee', no_endpoint = 'platform_settings', employee_id = employee_id)
	else:
		user = User.query.get(employee_id)
		db.session.delete(user)
		try:
			db.session.commit()
		except:
			db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/change_company_code", methods = ['GET', 'POST'])
@login_required
def change_company_code():
	form = ChangeCompanyCodeForm(csrf_enabled = False)
	if form.validate_on_submit():
		company_code = form.company_code.data
		company = Company.query.get(current_user.company_id)
		company.company_code = company_code
		try:
			db.session.commit()
		except:
			db.session.rollback()
	return render_template("change_company_code.html", form = form)

@app.template_global()
def get_roles_with_permission(permission):
	permission = Permission.query.filter_by(name = permission).first()
	roles_allowed = [role for role in permission.roles if role.company_id == current_user.company_id]
	return roles_allowed

@app.route("/authorize_role/<int:role_id>/<string:permission_name>", methods = ['GET', 'POST'])
@login_required
def authorize_role(role_id, permission_name):
	permission = Permission.query.filter_by(name = permission_name).first()
	role = Role.query.get(role_id)
	role.permissions.append(permission)
	try:
		db.session.commit()
	except:
		db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/forbid_role/<int:role_id>/<string:permission_name>", methods = ['GET', 'POST'])
@login_required
def forbid_role(role_id, permission_name):
	permission = Permission.query.filter_by(name = permission_name).first()
	role = Role.query.get(role_id)
	permission.roles.remove(role)
	try:
		db.session.commit()
	except:
		db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/delete_role/<int:role_id>/<string:decision>", methods = ['GET', 'POST'])
@login_required
def delete_role(role_id, decision):
	if decision == "PENDING":
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS ROLE?", yes_endpoint = 'delete_role', no_endpoint = 'platform_settings', role_id = role_id)
	else:
		for user in User.query.all():
			if user.role_id == role_id:
				user.role_id = 0
				try:
					db.session.commit()
				except:
					db.session.rollback()
		role = Role.query.get(role_id)
		db.session.delete(role)
		try:
			db.session.commit()
		except:
			db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/delete_department/<int:department_id>/<string:decision>", methods = ['GET', 'POST'])
@login_required
def delete_department(department_id, decision):
	if decision == "PENDING":
		return render_template("are_you_sure_message.html", confirmation_message = "ARE YOU SURE YOU WANT TO DELETE THIS DEPARTMENT?", yes_endpoint = 'delete_department', no_endpoint = 'platform_settings', department_id = department_id)
	else:
		for user in User.query.all():
			if user.department_id == department_id:
				user.department_id = 0
				try:
					db.session.commit()
				except:
					db.session.rollback()
		department = Department.query.get(department_id)
		db.session.delete(department)
		try:
			db.session.commit()
		except:
			db.session.rollback()
	return redirect(url_for('platform_settings'))

@app.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))
