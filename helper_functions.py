from app import db, mail
from models import *
import time
import random
from flask_mail import Mail, Message

def get_standard_tasks(service, company_id):
	procedure = Procedure.query.filter_by(service = service, company_id = company_id).first()
	return sorted(procedure.standard_tasks.all(), key = lambda standard_task: standard_task.step_number)

def get_all_procedures(company_id):
	procedures = Procedure.query.filter(Procedure.company_id == company_id).all()
	return procedures

def get_services(company_id):
	services = Service.query.filter(Service.company_id == company_id).all()
	return [service.name for service in services]

def get_departments(company_id):
	company = Company.query.get(company_id)
	departments = company.departments.all()
	return [department.name for department in departments]

def get_roles(company_id):
	company = Company.query.get(company_id)
	roles = company.roles.all()
	return [role.name for role in roles]

def get_active_orders(company_id):
	active_orders = Order.query.filter(Order.company_id == company_id, Order.completion_status < 100.0).all()
	return active_orders

def get_number_of_active_orders(company_id):
	return len(get_active_orders(company_id))

def get_completed_orders(company_id):
	completed_orders = Order.query.filter(Order.company_id == company_id, Order.completion_status == 100.0).all()
	return completed_orders

def get_number_of_completed_orders(company_id):
	return len(get_completed_orders(company_id))

def is_not_a_registered_department(name, company):
	departments = company.departments.all()
	if not any(department.name == name for department in departments):
		return True
	return False

def is_not_a_registered_role(name, company):
	roles = company.roles.all()
	if not any(role.name == name for role in roles):
		return True
	return False

def is_a_registered_service(name, company_id):
	match = Service.query.filter_by(name = name, company_id = company_id).first()
	if not match:
		return False
	return True

def registered_with_departments(company):
	if company.departments.all():
		return True
	return False

def registered_with_roles(company):
	if company.roles.all():
		return True
	return False

def are_registered_departments(departments):
	departments = [department.lower() for department in departments.split(", ")]
	registered_departments = [department.name.lower() for department in Department.query.all()]
	for department in departments:
		if department not in registered_departments:
			return False
	return True

def are_registered_roles(roles):
	roles = [role.lower() for role in roles.split(", ")]
	registered_roles = [role.name.lower() for role in Role.query.all()]
	for role in roles:
		if role not in registered_roles:
			return False
	return True

def get_standard_tasks_for_order(service_name, company_id):
	standard_tasks = get_standard_tasks(service_name, company_id)
	tasks = []
	for standard_task in standard_tasks:
		task = Task(title = standard_task.title, departments = standard_task.departments, roles = standard_task.roles, description = standard_task.description, step_number = standard_task.step_number, status = 0)
		db.session.add(task)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		tasks.append(task)
	return tasks

def reset_completion_status_for_order(order_id):
	order = Order.query.get(order_id)
	all_tasks = order.tasks.all()
	total = len(all_tasks)
	completed = 0
	for task in all_tasks:
		if task.status == 1:
			completed += 1
	order.completion_status = round((completed/total)*100, 1)
	try:
		db.session.commit()
	except:
		db.session.rollback()

def get_tasks_in_order(order):
	return sorted(order.tasks.all(), key = lambda task: task.step_number)

def get_incomplete_tasks_in_order(order):
	incomplete_tasks = []
	all_tasks = get_tasks_in_order(order)
	for task in all_tasks:
		if task.status == 0:
			incomplete_tasks.append(task)
	return incomplete_tasks

def set_task_as_completed(task_id):
	task = Task.query.get(task_id)
	task.status = 1
	try:
		db.session.commit()
	except:
		db.session.rollback()

def reset_step_number_for_tasks_in_order_after_deletion(order_id):
	order = Order.query.get(order_id)
	tasks = get_tasks_in_order(order)
	step_number = 1
	for task in tasks:
		task.step_number = step_number
		try:
			db.session.commit()
			step_number += 1
		except:
			db.session.rollback()

def reset_step_number_for_tasks_in_procedure_after_deletion(service_name, company_id):
	procedure = Procedure.query.filter_by(service = service_name, company_id = company_id)
	standard_tasks = get_standard_tasks(service_name, company_id)
	step_number = 1
	for standard_task in standard_tasks:
		standard_task.step_number = step_number
		try:
			db.session.commit()
			step_number += 1
		except:
			db.session.rollback()

def reset_step_number_for_tasks_in_order_after_insertion(order_id, current_step_number, new_task):
	order = Order.query.get(order_id)
	tasks = get_tasks_in_order(order).copy()
	tasks.pop(-1)
	tasks.insert(current_step_number - 1, new_task)
	step_number = 1
	for task in tasks:
		task.step_number = step_number
		try:
			db.session.commit()
			step_number += 1
		except:
			db.session.rollback()

def get_relevant_people_for_task(task, current_user):
	departments = task.departments.split(", ")
	relevant_people = []
	for department_name in departments:
		department = Department.query.filter_by(name=department_name, company_id = current_user.company_id).first()
		members = User.query.filter(User.department_id == department.id).all()
		relevant_people.extend(members)
	relevant_people.sort(key = lambda user: user.email.lower()[0])
	return relevant_people

def get_people_in_charge_for_task(task, current_user):
	roles = task.roles.split(", ")
	people_in_charge = []
	for role_name in roles:
		role = Role.query.filter_by(name = role_name, company_id = current_user.company_id).first()
		people = User.query.filter(User.role_id == role.id).all()
		people_in_charge.extend(people)
	people_in_charge.sort(key = lambda user: user.email.lower()[0])
	return people_in_charge

def get_tasks_for_user(current_user):
	tasks = current_user.tasks
	return tasks

def get_number_of_tasks_for_user(current_user):
	return len(get_tasks_for_user(current_user))

def get_number_of_completed_tasks_for_user(current_user):
	tasks = get_tasks_for_user(current_user)
	number_of_completed_tasks = 0
	for task in tasks:
		if task.status == 1:
			number_of_completed_tasks += 1
	return number_of_completed_tasks

def calculate_performance_point_for_user(current_user):
	number_of_tasks = get_number_of_tasks_for_user(current_user)
	number_of_completed_tasks = get_number_of_completed_tasks_for_user(current_user)
	if number_of_tasks:
		point = round((number_of_completed_tasks / number_of_tasks) * 100, 1)
	else: point = 100.00
	return point

def reset_performance_point_for_user(current_user):
	performance_point = calculate_performance_point_for_user(current_user)
	current_user.performance_point = performance_point
	try:
		db.session.commit()
	except:
		db.session.rollback()

def get_tasks_for_department(department_name, company_id):
	orders_in_company = Order.query.filter(Order.company_id == company_id).all()
	order_ids_in_company = [order.id for order in orders_in_company]
	tasks_in_company = Task.query.filter(Task.order_id in order_ids_in_company).all()	
	tasks_for_department = []
	for task in tasks_in_company:
		if department_name in task.departments.split(", "):
			tasks_for_department.append(task)
	return tasks_for_department

def get_number_of_tasks_for_department(department_name, company_id):
	return len(get_tasks_for_department(department_name, company_id))

def get_number_of_completed_tasks_for_department(department_name, company_id):
	tasks_for_department = get_tasks_for_department(department_name, company_id)
	number_of_completed_tasks = 0
	for task in tasks_for_department:
		if task.status == 1:
			number_of_completed_tasks += 1
	return number_of_completed_tasks

def reset_performance_point_for_departments_in_task(task_id, company_id):
	task = Task.query.get(task_id)
	department_names = task.departments.split(", ")
	for department_name in department_names:
		number_of_tasks = len(get_tasks_for_department(department_name, company_id))
		if number_of_tasks:
			performance_point = round((get_number_of_completed_tasks_for_department(department_name, company_id) / number_of_tasks) * 100, 1)
		else: performance_point = 100.00
		department = Department.query.filter_by(name = department_name, company_id = company_id).first()
		department.performance_point = performance_point
		try:
			db.session.commit()
		except:
			db.session.rollback()

def reset_updated_time_for_order(order_id):
	order = Order.query.get(order_id)
	order.time_updated = time.asctime()
	try:
		db.session.commit()
	except:
		db.session.rollback()

def get_employees_ranking_board(company_id):
	employees = sorted(User.query.filter(User.company_id == company_id).all(), 
		key = lambda employee: (get_number_of_completed_tasks_for_user(employee), employee.performance_point), 
		reverse = True)
	ranking_board = []
	rank = 1
	for employee in employees:
		performance_point = employee.performance_point
		info = (rank, employee.name, performance_point, get_number_of_completed_tasks_for_user(employee))
		ranking_board.append(info)
		rank += 1
	return ranking_board

def get_departments_ranking_board(company_id):
	departments = sorted(Department.query.filter(Department.company_id == company_id).all(), 
		key = lambda department: (get_number_of_completed_tasks_for_department(department.name, company_id), department.performance_point), 
		reverse = True)
	ranking_board = []
	rank = 1
	for department in departments:
		performance_point = department.performance_point
		info = (rank, department.name, department.performance_point, get_number_of_completed_tasks_for_department(department.name, company_id))
		ranking_board.append(info)
		rank += 1
	return ranking_board

def get_proportions_for_services(company_id):
	orders = Order.query.filter(Order.company_id == company_id).all()
	services_ordered = [order.service for order in orders]
	all_services = [service.name for service in Service.query.filter(Service.company_id == company_id).all()]
	proportions = []
	if services_ordered:
		for service in all_services:
			proportions.append((service, str(round(services_ordered.count(service) / len(services_ordered) * 100, 1)) + "%"))
		proportions.sort(key = lambda info: info[1], reverse = True)
	else:
		for service in all_services:
			proportions.append((service, "0.00%"))
	return proportions

def get_service_filtered_active_orders(company_id, service_name):
	filtered_active_orders = []
	if service_name:
		active_orders = get_active_orders(company_id)
		for order in active_orders:
			if order.service == service_name:
				filtered_active_orders.append(order)
	return filtered_active_orders

def get_service_filtered_completed_orders(company_id, service_name):
	filtered_completed_orders = []
	if service_name:
		completed_orders = get_completed_orders(company_id)
		for order in completed_orders:
			if order.service == service_name:
				filtered_completed_orders.append(order)
	return filtered_completed_orders

def get_client_filtered_active_orders(company_id, client_name):
	filtered_active_orders = []
	active_orders = get_active_orders(company_id)
	if client_name != 'All':
		for order in active_orders:
			if order.client_name == client_name:
				filtered_active_orders.append(order)
	else:
		filtered_active_orders.extend(active_orders)
	return filtered_active_orders

def get_client_filtered_completed_orders(company_id, client_name):
	filtered_completed_orders = []
	completed_orders = get_completed_orders(company_id)
	if client_name != 'All':
		for order in completed_orders:
			if order.client_name == client_name:
				filtered_completed_orders.append(order)
	else:
		filtered_completed_orders.extend(completed_orders)
	return filtered_completed_orders

def get_time_created_filtered_active_orders(company_id, day, month, year):
	filtered_active_orders = []
	active_orders = get_active_orders(company_id)
	if day == 'Not Sure' and month == 'Not Sure' and year == 'Not Sure':
			filtered_active_orders.extend(active_orders)
	else:
		for order in active_orders:
			time_created = order.time_created
			if day != 'Not Sure':
				recorded_day = time_created.split()[2]
			else:
				recorded_day = 'Not Sure'
			if month != 'Not Sure':
				recorded_month = time_created.split()[1]
			else:
				recorded_month = 'Not Sure'
			if year != 'Not Sure':
				recorded_year = time_created.split()[4]
			else:
				recorded_year = 'Not Sure'
			if (recorded_day == day and recorded_month == month and recorded_year == year):
				filtered_active_orders.append(order)
	return filtered_active_orders

def get_time_completed_filtered_completed_orders(company_id, day, month, year):
	filtered_completed_orders = []
	completed_orders = get_completed_orders(company_id)
	if day == 'Not Sure' and month == 'Not Sure' and year == 'Not Sure':
			filtered_completed_orders.extend(completed_orders)
	else:
		for order in completed_orders:
			time_completed = order.time_completed
			if day != 'Not Sure':
				recorded_day = time_completed.split()[2]
			else:
				recorded_day = 'Not Sure'
			if month != 'Not Sure':
				recorded_month = time_completed.split()[1]
			else:
				recorded_month = 'Not Sure'
			if year != 'Not Sure':
				recorded_year = time_completed.split()[4]
			else:
				recorded_year = 'Not Sure'
			if recorded_day == day and recorded_month == month and recorded_year == year:
				filtered_completed_orders.append(order)
	return filtered_completed_orders

def generate_temporary_password():
	characters = 'qwertyuiopasdfghjklzxcvbnm1234567890QWERTYUIOPASDFGHJKLZXCVBNM!@#$%^&*()+'
	password = ""
	for _ in range(10):
		character = characters[random.randrange(0, len(characters))]
		password += character
	return password

def add_participant_to_task(task_id, user_id, current_user):
	task = Task.query.get(task_id)
	user = User.query.get(user_id)
	if user not in task.users:
		task.users.append(user)
		try:
			db.session.commit()
		except:
			db.session.rollback()

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
		content = f"You have been assigned a new task titled '{task_title}' in the order titled '{service_name}', created on {order_creation_time}, for the client called '{client_name}', by {author} ({author_email}) from the {author_department} department. This task is step number {step_number} in the order."

		reset_updated_time_for_order(task.order_id)

		notification = Notification(time_created = notification_creation_time, title = "Job Assignment", message = content, redirection = f"/manage_order/{order_id}")
		db.session.add(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()

		user.notifications.append(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		receiver_email = user.email
		msg = Message(f'Job Assignment', sender = (f'{company_name}', 'juststartplatform@aol.com'), recipients = [receiver_email])
		msg.body = content + '\n\nGo to Account Info on JS Platform for more information.'
		mail.send(msg)
	

def notify_people_of_first_task(task, people, current_user):
	task_title = task.title
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
	content = f"A new order titled '{service_name}' has been created on {order_creation_time} for the client called '{client_name}' by {author} ({author_email}) from the {author_department} department. You are responsible for the first task, which is called '{task_title}'. Begin working on the task now."

	notification = Notification(time_created = notification_creation_time, title = "Job Assignment", message = content, redirection = f"/manage_order/{order_id}")
	db.session.add(notification)
	try:
		db.session.commit()
	except:
		db.session.rollback()

	for person in people:
		person.notifications.append(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		receiver_email = person.email
		msg = Message(f'Job Assignment', sender = (f'{company_name}', 'juststartplatform@aol.com'), recipients = [receiver_email])
		msg.body = content + '\n\nGo to Account Info on JS Platform for more information.'
		mail.send(msg)

def notify_people_on_next_task(task, people):
	task_title = task.title
	step_number = task.step_number
	order_id = task.order_id
	order = Order.query.get(order_id)
	service_name = order.service
	client_name = order.client_name
	order_creation_time = order.time_created
	notification_creation_time = time.asctime()
	company_name = Company.query.get(order.company_id).name
	if step_number > 2:
		content = f"Steps 1 to {step_number} in the order titled '{service_name}', created on {order_creation_time}, for the client called '{client_name}' have been completed. You can now begin working on step {step_number + 1} titled {task_title}."
	else:
		content = f"The 1st step in the order titled '{service_name}', created on {order_creation_time}, for the client called '{client_name}' has been completed. You can now begin working on the 2nd task titled {task_title}."
	notification = Notification(time_created = notification_creation_time, title = "Job Assignment", message = content, redirection = f"/manage_order/{order_id}")
	db.session.add(notification)
	try:
		db.session.commit()
	except:
		db.session.rollback()

	for person in people:
		person.notifications.append(notification)
		try:
			db.session.commit()
		except:
			db.session.rollback()
		receiver_email = person.email
		msg = Message(f'Job Assignment', sender = (f'{company_name}', 'juststartplatform@aol.com'), recipients = [receiver_email])
		msg.body = content + '\n\nGo to Account Info on JS Platform for more information.'
		mail.send(msg)
