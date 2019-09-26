import json
import os
import time
import datetime

from flask import render_template, url_for, flash, redirect, request, jsonify, send_from_directory
from manage import app, db, bcrypt, account, TOKEN_EXPIRED, PASSWORD_TOKEN_EXPIRED
from manage.forms import RegisterationForm, LoginForm
from manage.models import User, Service, ClientItem, AdminItem, UserService, AItem, CItem, Country
from flask_login import login_user, current_user, logout_user, login_required
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug import secure_filename

safe = URLSafeTimedSerializer("this is secret!")
def check_admin():
    if current_user.is_authenticated:
        role = current_user.role
        if role == 1:
            return False
    return True

def check_client():
    if current_user.is_authenticated:
        role = current_user.role
        if role == 0:
            return False
    return True

@app.route("/page-error")
def page_error():
    return render_template('500.html')

@app.context_processor
def check_service():
    def check_active(user_service_id):
        user_service = UserService.query.filter_by(id=user_service_id).first()
        a_items = user_service.a_items
        flag = False
        for a_item in a_items:
            if a_item.finished == False:
                flag = True
        return flag
    def check_user_active(user_id):
        user = User.query.filter_by(id=user_id).first()
        user_services =user.user_services
        flag = False
        for user_service in user_services:
            a_items = user_service.a_items
            for a_item in a_items:
                if a_item.finished == False:
                    flag = True
        return flag
    return dict(check_active=check_active,check_user_active=check_user_active)


@app.route("/")
@app.route("/home")
def home():
    if current_user.is_authenticated:
        if current_user.role == 1:
            completed_task = 0
            incom_count = 0
            clients = User.query.filter_by(role=0)
            for client in clients:
                user_services = client.user_services
                for user_service in user_services:
                    c_items = user_service.c_items
                    flag = False
                    for c_item in c_items:
                        if c_item.finished == False:
                            flag = True
                            incom_count += 1
                    if flag == True:
                        completed_task += 1
            if completed_task > 0:
                completed_task -= 1
            if incom_count > 0:
                incom_count -= 1

            return render_template('admin/home.html',active = completed_task, incom=incom_count,clients=clients)
        else:
            current_user_id = current_user.id
            user = User.query.filter_by(id=current_user_id).first()
            user_services = user.user_services
            completed_task = 0
            incom_count = 0
            for user_service in user_services:
                c_items = user_service.c_items
                flag = False
                for c_item in c_items:
                    if c_item.finished == False:
                        flag = True
                        incom_count += 1
                if flag == True:
                    completed_task += 1
            if completed_task > 0:
                completed_task -= 1
            if incom_count > 0:
                incom_count -= 1



            return render_template('client/home.html',active = completed_task, incom=incom_count, client= user)
    else:
        return redirect(url_for('login'))
        
# register user
@app.route("/register", methods=['GET','POST'])
def register():
    form = RegisterationForm()
    if form.validate_on_submit():
        already_user = User.query.filter_by(email=form.username.data).first()
        if already_user:
            flash('That user was taken. Please choose a different one!', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            user = User(email=form.username.data, password = hashed_password)
            db.session.add(user)
            db.session.commit()
            flash(f'Account created for {form.username.data}!', 'success')
            return redirect(url_for('home'))
    return render_template('register.html', title='Register', form=form)

#send verificaion code to client
def send_message(link,email):
    if not account.is_authenticated:
        account.authenticate(scopes=['basic','message_all'])
    mailbox = account.mailbox()
    inbox = mailbox.inbox_folder()
    m = mailbox.new_message()
    m.to.add(email)
    m.subject = 'Please verify your email'
    m.body = 'Hi the verification link is : ' + link + ' \n This link will be expired after 10 hours'
    m.send()

# login function
@app.route("/login", methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            if user.verified == True:
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(url_for(next_page)) if next_page else redirect(url_for('home'))
            else:
                flash('You need to confirm your email!','danger')
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html', title='Login', form=form)

# resend verification to client
@app.route("/send-verification/<email>",methods=['POST'])
@login_required
def send_verification(email):
    res = {}
    try:
        user = User.query.filter_by(email=email).first()
        if user:
            token = safe.dumps(email, salt='email-confirm')
            link = url_for('confirm_email', token=token, _external=True)
            send_message(link,user.email)
            res['response'] = 'success'
        else:
            res['response'] = 'no user'
    except TimeoutError:
        res['response'] = 'error'
    return jsonify(res)
        

@app.route("/confirm-email/<token>")
def confirm_email(token):
    try:
        email = safe.loads(token, salt='email-confirm', max_age=TOKEN_EXPIRED)
        print(email)
        user = User.query.filter_by(email=email).first()
        if user == None:
            flash('You are not a user !', 'danger')
            return redirect(url_for('login'))

        if user.verified == True:
            flash('already confirmed! ', 'warning')
            return redirect(url_for('login'))

        user.verified = True
        db.session.add(user)
        db.session.commit()
        flash('Successfully confirmed! ', 'success')
        return redirect(url_for('reset_password', user_id=user.id,token=token))
    except SignatureExpired:
        flash('Token expired! Please contact to administrator', 'danger')
    return redirect(url_for('login'))

@app.route("/forgot-password")
def forgot_password():
    return render_template('forgot.html')

#send verificaion link for reset password
def send_reset_message(link,email):
    if not account.is_authenticated:
        account.authenticate(scopes=['basic','message_all'])
    mailbox = account.mailbox()
    m = mailbox.new_message()
    m.to.add(email)
    m.subject = 'Please follow this link'
    m.body = 'Hi the reset link is : ' + link + ' \n This link will be expired after 1 minute'
    m.send()

@app.route("/confirm-reset/<token>")
def confirm_reset(token):
    try:
        email = safe.loads(token, salt='email-confirm', max_age=PASSWORD_TOKEN_EXPIRED)
        print(email)
        user = User.query.filter_by(email=email).first()
        if user == None or user.verified != True:
            flash('You are not a user !', 'danger')
            return redirect(url_for('login'))

        return redirect(url_for('reset_password', user_id=user.id, token=token))
    except SignatureExpired:
        flash('Token expired! Please resend to your email', 'danger')
    return redirect(url_for('login'))

@app.route("/send-reset-password",methods=['POST'])
def send_reset_password():
    email = request.form['email']
    user = User.query.filter_by(email=email).first()
    if user:
        token = safe.dumps(email, salt='email-confirm')
        link = url_for('confirm_reset', token=token, _external=True)
        send_reset_message(link,user.email)
        flash('Successfully sent! please go to your email inbox and follow the link','success')
    else:
        flash('You are not a user !','danger')
    return redirect(url_for('forgot_password'))

@app.route("/send-reset-password-email",methods=['POST'])
def send_reset_password_email():
    user_id = request.form['user_id']
    res = {}
    try:
        user = User.query.filter_by(id=user_id).first()
        if user:
            token = safe.dumps(user.email, salt='email-confirm')
            link = url_for('confirm_reset', token=token, _external=True)
            send_reset_message(link,user.email)
        else:
            flash('You are not a user !','danger')
        res['response'] = 'success'
    except Exception:
        res['response'] = 'error'
    return jsonify(res)

#logout function
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/reset-password/<user_id>/<token>",methods=['GET','POST'])
def reset_password(user_id,token):
    if request.method == 'GET':
        return render_template('reset.html',user_id=user_id,token=token)
    else:
        cur_id = request.form['user_id']
        try:
            email = safe.loads(token, salt='email-confirm', max_age=PASSWORD_TOKEN_EXPIRED)
            print(email)
            user = User.query.filter_by(email=email).first()
            if user == None or user.verified != True:
                flash('You are not a user !', 'danger')
                return redirect(url_for('login'))
            new_password = request.form['newPassword']
            confirm_password = request.form['confirmPassword']
            if new_password != confirm_password:
                flash('Confirm Password doesn\'t match', 'danger')
                redirect(url_for('reset_password', user_id=cur_id,token=token))
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            user.password = hashed_password
            db.session.commit()

        except SignatureExpired:
            flash('token expired!', 'danger')
            return redirect(url_for('login'))

    return redirect(url_for('login'))

@app.route("/a-item-detail",methods=['POST'])
@login_required
def a_item_detail():
    item_id = request.form['item_id']
    a_item = AItem.query.filter_by(id=item_id).first()
    res = {}
    res['form_text'] = a_item.form_text
    res['filename'] = a_item.filename
    date_time = a_item.date
    date_str = ''
    if date_time:
        date_str = date_time.strftime("%Y-%m-%dT%H:%M")
    res['date'] = date_str
    res['checked'] = a_item.checked


    user_service_id = a_item.user_service_id
    user_service = UserService.query.filter_by(id=user_service_id).first()
    service = Service.query.filter_by(id=user_service.service_id).first()
    admin_items = service.admin_items
    for admin_item in admin_items:
        if admin_item.name == a_item.name and admin_item.function == a_item.function:
            matched_id = admin_item.matched_item
            if matched_id != 0:
                client_item = ClientItem.query.filter_by(id=matched_id).first()
                c_item = CItem.query.filter_by(name=client_item.name).first()
                res['client_form_text'] = c_item.form_text
                res['client_filename'] = c_item.filename
                date_str = ''
                if c_item.date:
                    date_str = c_item.date.strftime("%Y-%m-%dT%H:%M")
                res['client_date'] = date_str
                res['client_checked'] = c_item.checked

    return jsonify(res)

@app.route("/c-item-detail",methods=['POST'])
@login_required
def c_item_detail():
    item_id = request.form['item_id']
    c_item = CItem.query.filter_by(id=item_id).first()
    res = {}
    res['form_text'] = c_item.form_text
    res['filename'] = c_item.filename
    date_time = c_item.date
    date_str = ''
    if date_time:
        date_str = date_time.strftime("%Y-%m-%dT%H:%M")
    res['date'] = date_str
    res['checked'] = c_item.checked


    user_service_id = c_item.user_service_id
    user_service = UserService.query.filter_by(id=user_service_id).first()
    service = Service.query.filter_by(id=user_service.service_id).first()
    client_items = service.client_items
    for client_item in client_items:
        if client_item.name == c_item.name and client_item.function == c_item.function:
            matched_id = client_item.matched_item
            if matched_id != 0:
                admin_item = AdminItem.query.filter_by(id=matched_id).first()
                a_item = AItem.query.filter_by(name=admin_item.name).first()
                res['admin_form_text'] = a_item.form_text
                res['admin_filename'] = a_item.filename
                date_str = ''
                if a_item.date:
                    date_str = a_item.date.strftime("%Y-%m-%dT%H:%M")
                res['admin_date'] = date_str
                res['admin_checked'] = a_item.checked

    return jsonify(res)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route("/item-finish",methods=['POST'])
@login_required
def item_finish():
    res = {}
    now = datetime.datetime.now()
    try:
        item_id = request.form['item_id']
        mode = request.form['mode']
        value = request.form['value']
        if int(mode) == 0:
            item = AItem.query.filter_by(id=item_id).first()
            c_item = get_matched_c_item(item_id,item.user_service_id)
            if int(value) == 0:
                item.finished = False
                if c_item != '':
                    c_item.finished = False
            else:
                item.finished = True
                item.finished_time = now
                if c_item !='':
                    c_item.finished = True
                    c_item.finished_time = now

        else:
            item = CItem.query.filter_by(id=item_id).first()
            a_item = get_matched_a_item(item_id,item.user_service_id)
            if int(value) == 0:
                item.finished = False
                if a_item:
                    a_item.finished = False
            else:
                item.finished = True
                item.finished_time = now
                if a_item:
                    a_item.finished = True
                    a_item.finished_time = now
        db.session.commit()
        res['response'] = 'success'
    except TimeoutError:
        db.session.commit()
        res['response'] = 'error'
    return jsonify(res)

@app.route("/set-date",methods=['POST'])
@login_required
def set_date():
    res = {}
    now = datetime.datetime.now()
    try:
        item_id = request.form['item_id']
        mode = request.form['mode']
        value = request.form['value']
        date_obj = datetime.datetime.strptime(value, '%Y-%m-%d')
        if int(mode) == 0:
            item = AItem.query.filter_by(id=item_id).first()
            item.date =date_obj
            item.finished =True
            item.finished_time =now
            c_item = get_matched_c_item(item_id,item.user_service_id)
            if c_item:
                c_item.date = date_obj
                c_item.finished = True
                c_item.finished_time = now
        else:
            item = CItem.query.filter_by(id=item_id).first()
            item.date =date_obj
            item.finished =True
            item.finished_time =now
            a_item = get_matched_a_item(item_id, item.user_service_id)
            if a_item:
                a_item.date = date_obj
                a_item.finished = True
                a_item.finished_time = now
        db.session.commit()
        res['response'] = 'success'
    except Exception:
        res['response'] = 'error'
    return jsonify(res)

def get_matched_a_item(item_id,user_service_id):
    c_item = CItem.query.filter_by(id=item_id).first()
    user_service = UserService.query.filter_by(id=user_service_id).first()
    service_id = user_service.service_id
    service = Service.query.filter_by(id=service_id).first()
    if service:
        for client_item in service.client_items:
            if client_item.name == c_item.name:
                admin_item_id = client_item.matched_item
                admin_item = AdminItem.query.filter_by(id=admin_item_id).first()
                if admin_item:
                    for a_item in user_service.a_items:
                        if a_item.name == admin_item.name:
                            print(a_item)
                            return a_item
    return ''

def get_matched_c_item(item_id,user_service_id):
    a_item = AItem.query.filter_by(id=item_id).first()
    user_service = UserService.query.filter_by(id=user_service_id).first()
    service_id = user_service.service_id
    service = Service.query.filter_by(id=service_id).first()
    if service:
        for admin_item in service.admin_items:
            if admin_item.name == a_item.name:
                client_item_id = admin_item.matched_item
                client_item = ClientItem.query.filter_by(id=client_item_id).first()
                if client_item:
                    for c_item in user_service.c_items:
                        if c_item.name == client_item.name:
                            print(c_item)
                            return c_item
    return ''


@app.route("/set-file",methods=['POST'])
@login_required
def set_file():
    res = {}
    now = datetime.datetime.now()
    try:
        user_service_id = request.form['user_service_id']
        item_id = request.form['item_id']
        mode = request.form['mode']
        file = request.files['file']
        item = None
        if int(mode) == 0:
            item = AItem.query.filter_by(id=item_id).first()
        else:
            item = CItem.query.filter_by(id=item_id).first()

        if file and allowed_file(file.filename):
            if item.filename:
                old_file = os.path.join(app.config['UPLOADS_PATH'], item.filename)
                if os.path.exists(old_file):
                    os.remove(old_file)
            filename = secure_filename(file.filename)
            file_name, file_extension = os.path.splitext(filename)
            timestr = time.strftime("%Y%m%d-%H%M%S") + "" + file_extension
            file.save(os.path.join(app.config['UPLOADS_PATH'], timestr))
            item.filename = timestr
            item.finished = True
            item.finished_time = now
            if int(mode) == 0:
                matched_item = get_matched_c_item(item_id,user_service_id)
                if matched_item.filename:
                    old_file = os.path.join(app.config['UPLOADS_PATH'], matched_item.filename)
                    if os.path.exists(old_file):
                        os.remove(old_file)
                matched_item.filename = timestr
                matched_item.finished = True
                matched_item.finished_time = now
            else:
                matched_item = get_matched_a_item(item_id,user_service_id)
                if matched_item.filename:
                    old_file = os.path.join(app.config['UPLOADS_PATH'], matched_item.filename)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                matched_item.filename = timestr
                matched_item.finished = True
                matched_item.finished_time = now

            print(timestr)

        db.session.commit()
        res['response'] = 'success'
    except TimeoutError:
        res['response'] = 'error'
    return jsonify(res)

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
@login_required
def download_file(filename):
    return send_from_directory(app.config['UPLOADS_PATH'], filename=filename, as_attachment=True)

@app.route('/download-a-file/<item_id>', methods=['GET', 'POST'])
@login_required
def download_file_by_a_id(item_id):
    item = AItem.query.filter_by(id=item_id).first()
    filename = item.filename
    if filename:
        return send_from_directory(app.config['UPLOADS_PATH'], filename=filename, as_attachment=True)
    else:
        flash("there is no file !", "warning")
        return redirect(url_for('home'))

@app.route('/download-c-file/<item_id>', methods=['GET', 'POST'])
@login_required
def download_file_by_c_id(item_id):
    item = CItem.query.filter_by(id=item_id).first()
    filename = item.filename
    if filename:
        return send_from_directory(app.config['UPLOADS_PATH'], filename=filename, as_attachment=True)
    else:
        flash("there is no file !", "warning")
        return redirect(url_for('home'))

@app.context_processor
def get_matched_item():
    def get_matched_a_item(item_id,user_service_id):
        c_item = CItem.query.filter_by(id=item_id).first()
        user_service = UserService.query.filter_by(id=user_service_id).first()
        service_id = user_service.service_id
        service = Service.query.filter_by(id=service_id).first()
        if service:
            for client_item in service.client_items:
                if client_item.name == c_item.name:
                    admin_item_id = client_item.matched_item
                    if admin_item_id != 0:
                        admin_item = AdminItem.query.filter_by(id=admin_item_id).first()
                        if admin_item:
                            for a_item in user_service.a_items:
                                if a_item.name == admin_item.name:
                                    print(a_item)
                                    return a_item
        return ''

    def get_matched_c_item(item_id,user_service_id):
        a_item = AItem.query.filter_by(id=item_id).first()
        user_service = UserService.query.filter_by(id=user_service_id).first()
        service_id = user_service.service_id
        service = Service.query.filter_by(id=service_id).first()
        if service:
            for admin_item in service.admin_items:
                if admin_item.name == a_item.name:
                    client_item_id = admin_item.matched_item
                    if client_item_id != 0:
                        client_item = ClientItem.query.filter_by(id=client_item_id).first()
                        if client_item:
                            for c_item in user_service.c_items:
                                if c_item.name == client_item.name:
                                    print(c_item)
                                    return c_item
        return ''
    return dict(get_matched_a_item=get_matched_a_item,get_matched_c_item=get_matched_c_item)

@app.route("/client-management")
@login_required
def client_management():
    if(check_admin()):
        return redirect(url_for('page_error'))
    clients = User.query.filter_by(role=0)
    services = Service.query.all()
    return render_template("admin/client-manage.html",clients=clients, services=services)

@app.route("/add-client", methods=['POST'])
@login_required
def add_client():
    if(check_admin()):
        return redirect(url_for('page_error'))
    name = request.form['name']
    email = request.form['email']
    company = ''
    tel = ''
    try:
        company = request.form['company']
    except Exception:
        pass
    try:
        tel = request.form['tel']
    except Exception:
        pass
    try:
        user = User(name = name,email = email,company = company,tel = tel,  password = " ")
        db.session.add(user)
        db.session.commit()
        flash("successfuly created !", "success")
        send_verification(user.email)
    except Exception:
        flash("put different user name !", "danger")

    return redirect(url_for('client_management'))


@app.route("/update-client", methods=['POST'])
@login_required
def update_client():
    cur_client = request.form['cur_client']
    name = request.form['name']
    email = request.form['email']
    company = ''
    tel = ''
    try:
        company = request.form['company']
    except Exception:
        pass
    try:
        tel = request.form['tel']
    except Exception:
        pass

    user = User.query.filter_by(id=cur_client).first()
    user.name = name
    user.email = email
    user.company = company
    user.tel = tel

    db.session.add(user)
    db.session.commit()
    flash("successfuly udpated !", "success")

    return redirect(url_for('client_management'))

@app.route("/detail-user", methods=['POST'])
@login_required
def detail_user():
    client_id = request.form['client_id']
    client = User.query.filter_by(id=client_id).first()
    res = {}
    if client:
        res['name'] = client.name
        res['email'] = client.email
        res['company'] = client.company
        res['tel'] = client.tel
        res['address1'] = client.address1
        res['address2'] = client.address2
        res['city'] = client.city
        res['state'] = client.state
        res['zip'] = client.zip
        res['country'] = client.country

    return jsonify(res)

@app.route("/delete-client", methods=['POST'])
@login_required
def delete_client():
    res = {}
    try:
        client_id = request.form['client_id']
        user = User.query.filter_by(id=client_id).first()
        user_services = user.user_services
        for user_service in user_services:
            user_service.delete()
        User.query.filter_by(id=int(client_id)).delete()
        db.session.commit()
        res['response'] = 'success'
        flash("successfuly deleted !", "success")
    except Exception:
        res['response'] = 'error'
    return jsonify(res)

@app.route("/service-management")
@login_required
def service_management():
    if(check_admin()):
        return redirect(url_for('page_error'))
    services = Service.query.all()
    return render_template("admin/service-manage.html", services=services)

@app.route("/edit-service/<service_id>")
@login_required
def edit_service(service_id):
    if(check_admin()):
        return redirect(url_for('page_error'))

    service = Service.query.filter_by(id=service_id).first()
    admin_items = None
    client_items = None
    if service:
        admin_items = service.admin_items
        client_items = service.client_items
        print(admin_items)
        print(client_items)
    return render_template("admin/service-edit.html", service=service,admin_items=admin_items,client_items=client_items)

@app.route("/add-service", methods=['POST'])
@login_required
def add_service():
    if(check_admin()):
        return redirect(url_for('page_error'))
    name = request.form['name']
    description = ''
    try:
        description = request.form['description']
    except Exception:
        pass
    
    service = Service(name=name,description=description)
    db.session.add(service)
    db.session.commit()
    
    print(service.id)
    print(service.name)
    print(service.description)
    
    return redirect(url_for('edit_service',service_id = service.id))

#add new item on service
@app.route("/add-item", methods=['POST'])
@login_required
def add_item():
    if(check_admin()):
        return redirect(url_for('page_error'))
    service_id = request.form['cur_service']
    name = request.form['name']
    function = request.form['type']
    mode = int(request.form['mode'])
    service = Service.query.filter_by(id=service_id).first()
    user_services = service.user_services
    if mode == 0:
        admin_item = AdminItem(name = name,item_type=True, service=service,function=function)
        db.session.add(admin_item)
        db.session.commit()
        for user_service in user_services:
            a_item = AItem(name=admin_item.name, item_type=admin_item.item_type, function=admin_item.function)
            user_service.a_items.append(a_item)
            db.session.add(a_item)
            db.session.commit()
    elif mode == 1:
        client_item = ClientItem(name = name,item_type=True, service=service,function=function)
        db.session.add(client_item)
        db.session.commit()
        for user_service in user_services:
            c_item = CItem(name=client_item.name, item_type=client_item.item_type, function=client_item.function)
            user_service.c_items.append(c_item)
            db.session.add(c_item)
            db.session.commit()
    elif mode == 2:
        admin_item = AdminItem(name = name,item_type=False, service=service,function=function)
        db.session.add(admin_item)
        db.session.commit()
        for user_service in user_services:
            a_item = AItem(name=admin_item.name, item_type=admin_item.item_type, function=admin_item.function)
            user_service.a_items.append(a_item)
            db.session.add(a_item)
            db.session.commit()
    elif mode == 3:
        client_item = ClientItem(name = name,item_type=False, service=service,function=function)
        db.session.add(client_item)
        db.session.commit()
        for user_service in user_services:
            c_item = CItem(name=client_item.name, item_type=client_item.item_type, function=client_item.function)
            user_service.c_items.append(c_item)
            db.session.add(c_item)
            db.session.commit()

    return redirect(url_for('edit_service',service_id = service_id))

#match admin and client items
@app.route("/join-item", methods=['POST'])
@login_required
def join_item():
    res = {}
    try:
        admin_id = request.form['admin_id']
        client_id = request.form['client_id']
        admin_item = AdminItem.query.filter_by(id=admin_id).first()
        admin_item.matched_item = client_id
        db.session.add(admin_item)
        db.session.commit()
        client_item = ClientItem.query.filter_by(id=client_id).first()
        client_item.matched_item = admin_id
        db.session.add(client_item)
        db.session.commit()
        res['response'] = 'success'
    except Exception:
        res['response'] = 'error'
    return jsonify(res)

@app.route("/unjoin-item", methods=['POST'])
@login_required
def unjoin_item():
    res = {}
    try:
        admin_id = request.form['admin_id']
        client_id = request.form['client_id']
        admin_item = AdminItem.query.filter_by(id=admin_id).first()
        admin_item.matched_item = 0
        db.session.add(admin_item)
        db.session.commit()
        client_item = ClientItem.query.filter_by(id=client_id).first()
        client_item.matched_item = 0
        db.session.add(client_item)
        db.session.commit()
        res['response'] = 'success'
    except Exception:
        res['response'] = 'error'
    return jsonify(res)

@app.route("/detail-item", methods=['POST'])
@login_required
def detail_item():
    item_id = request.form['item_id']
    mode = request.form['mode']
    res={}
    item = None
    if int(mode) == 0:
        item = AdminItem.query.filter_by(id=item_id).first()
    else:
        item = ClientItem.query.filter_by(id=item_id).first()
    if item:
        res['name'] = item.name
        res['function'] = item.function
    return jsonify(res)

@app.route("/edit-item", methods=['POST'])
@login_required
def edit_item():
    service_id = request.form['cur_service']
    mode = request.form['mode']
    item_id = request.form['item_id']
    item_mode = request.form['item_mode']
    item = None
    if int(item_mode) == 0:
        item = AdminItem.query.filter_by(id=item_id).first()
    else:
        item = ClientItem.query.filter_by(id=item_id).first()

    if int(mode) == 0:
        name = request.form['name']
        type = request.form['type']
        item.name = name
        item.type = type
        db.session.commit()
    else:
        matched_id = item.matched_item
        if int(item_mode) == 0:
            matched_item = ClientItem.query.filter_by(id=matched_id).first()
            if matched_item:
                matched_item.matched_item = 0
            AdminItem.query.filter_by(id=item_id).delete()
        else:
            matched_item = AdminItem.query.filter_by(id=matched_id).first()
            if matched_item:
                matched_item.matched_item = 0
            ClientItem.query.filter_by(id=item_id).delete()
        db.session.commit()
    return redirect(url_for('edit_service',service_id=service_id))

@app.route("/delete-service", methods=['POST'])
@login_required
def delete_service():
    if(check_admin()):
        return redirect(url_for('page_error'))
    res = {}
    try:
        service_id = request.form['service_id']
        service = Service.query.filter_by(id=service_id).first()
        admin_items = service.admin_items
        client_items = service.client_items
        user_services = service.user_services
        for admin_item in admin_items:
            db.session.delete(admin_item)
        for client_item in client_items:
            db.session.delete(client_item)
        for user_service in user_services:
            a_items = user_service.a_items
            for a_item in a_items:
                db.session.delete(a_item)
            c_items = user_service.c_items
            for c_item in c_items:
                db.session.delete(c_item)
            db.session.delete(user_service)
        Service.query.filter_by(id=service_id).delete()
        db.session.commit()
        res['response'] = 'success'
    except TimeoutError:
        res['response'] = 'error'
    return jsonify(res)


def check_service_active(user_service_id):
    user_service = UserService.query.filter_by(id=user_service_id).first()
    a_items = user_service.a_items
    flag = False
    for a_item in a_items:
        if a_item.finished == False:
            flag = True
    return flag

@app.route("/assign-service", methods=['POST'])
@login_required
def assign_service():
    if(check_admin()):
        return redirect(url_for('page_error'))
    res = {}
    service_id = request.form['service_id']
    client_id = request.form['client_id']
    project = request.form['project']
    user = User.query.filter_by(id=client_id).first()
    service = Service.query.filter_by(id=int(service_id)).first()
    admin_items = service.admin_items
    client_items = service.client_items

    user_service = UserService(name=service.name, user_id=user.id, service_id=service.id,project_name=project)
    db.session.add(user_service)
    db.session.commit()

    user.user_services.append(user_service)
    db.session.commit()
    service.user_services.append(user_service)
    db.session.commit()

    for admin_item in admin_items:
        a_item = AItem(name=admin_item.name, item_type=admin_item.item_type, function=admin_item.function)
        user_service.a_items.append(a_item)
        db.session.add(a_item)
        db.session.commit()
    for client_item in client_items:
        c_item = CItem(name=client_item.name, item_type=client_item.item_type, function=client_item.function)
        user_service.c_items.append(c_item)
        db.session.add(c_item)
        db.session.commit()
    res['response'] = 'success'
    flash("successfully added !", "success")

    return jsonify(res)

@app.route("/admin-management")
@login_required
def admin_management():
    if(check_admin()):
        return redirect(url_for('page_error'))
    admins = User.query.filter_by(role=1)
    return render_template("admin/admin-manage.html",admins=admins)

@app.route("/send-invite", methods=['POST'])
@login_required
def send_invite():
    if(check_admin()):
        return redirect(url_for('page_error'))
    name = request.form['name']
    email = request.form['email']
    company = ''
    tel = ''
    try:
        company = request.form['company']
    except Exception:
        pass
    try:
        tel = request.form['tel']
    except Exception:
        pass

    user = User(name=name, email=email, company=company, tel=tel,password="", role=1)
    db.session.add(user)
    db.session.commit()
    send_verification(user.email)
    flash("successfuly invited !", "success")

    return redirect(url_for('admin_management'))

@app.route("/resend-invite", methods=['POST'])
@login_required
def resend_invite():
    if(check_admin()):
        return redirect(url_for('page_error'))
    admin_id = request.form['admin_id']
    admin = User.query.filter_by(id=admin_id).first()
    send_verification(admin.email)
    res = {}
    res['response'] = 'success'

    return jsonify(res)

@app.route("/client-detail-page")
@login_required
def client_detail_page():
    if(check_client()):
        return redirect(url_for('page_error'))
    client = User.query.filter_by(id=current_user.id).first()
    country_name = ''
    country = client.country
    if country:
        country_obj = Country.query.filter_by(id=country).first()
        country_name = country_obj.name
    countries = Country.query.all()

    return render_template('client/client-detail.html',countries=countries,country_name=country_name, client = client)

@app.route("/save-detail", methods=['POST'])
@login_required
def save_detail():
    try:
        client_id = request.form['clientID']
        name = request.form['fullName']
        address1 = request.form['address1']
        address2 = request.form['address2']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']
        country=''
        if 'country' in request.form:
            country = request.form['country']

        user = User.query.filter_by(id=client_id).first()
        user.name = name
        user.address1 = address1
        user.address2 = address2
        user.city = city
        user.state = state
        user.zip = zip
        user.country = country

        db.session.commit()
    except Exception:
        pass
    return redirect(url_for('client_detail_page'))

@app.route("/change-password", methods=['POST'])
@login_required
def change_password():
    cur_id = request.form['clientID']
    user = User.query.filter_by(id=cur_id).first()
    cur_password = request.form['curPassword']
    new_password = request.form['newPassword']
    confirm_password = request.form['confirmPassword']
    if new_password != confirm_password:
        flash('Confirm Password doesn\'t match', 'danger')
    if bcrypt.check_password_hash(user.password, cur_password):
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
    else:
        flash('Wrong Password!', 'danger')
    return redirect(url_for('client_detail_page'))

@app.route("/report-page")
@login_required
def report_page():
    if(check_client()):
        return redirect(url_for('page_error'))
    user = User.query.filter_by(id=current_user.id).first()
    user_services = user.user_services
    services = []
    for user_service in user_services:
        service_item ={}
        service_item['user_service'] = user_service.name
        service_item['project'] = user_service.project_name
        service_item['company'] = user.company
        c_items = user_service.c_items

        service_item['items'] = c_items
        services.append(service_item)

    return render_template('client/report.html',services=services)


@app.route("/history-page")
@login_required
def history_page():
    if(check_admin()):
        return redirect(url_for('page_error'))

    users_list = User.query.filter_by(role=0).all()
    users = []
    for user in users_list:
        user_services = user.user_services
        if user_services:
            services = []
            for user_service in user_services:
                service_item ={}
                service_item['user_service'] = user_service.name
                service_item['project'] = user_service.project_name
                service_item['company'] = user.company
                c_items = user_service.c_items

                service_item['items'] = c_items
                services.append(service_item)
            users.append(services)
    print(users)
    return render_template('admin/history.html',users=users)


@app.route("/service-detail")
@login_required
def service_detail():
    if(check_admin()):
        return redirect(url_for('page_error'))

    return render_template("admin/service-detail.html")