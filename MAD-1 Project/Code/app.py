import sqlite3
import os
from flask import Flask
from flask import render_template, url_for, redirect
from flask import request, jsonify
from jinja2 import Template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, bindparam, desc, or_, LargeBinary
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
from sqlalchemy.types import Date
from datetime import date, datetime
import base64
from sqlalchemy.ext.declarative import declarative_base
from io import BytesIO

conn = sqlite3.connect('groceries.sqlite3', detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, isolation_level=None, check_same_thread=False)
conn.text_factory = str
conn.close()

current_dir=os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
engine = create_engine('sqlite:///groceries.sqlite3')

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///"+ os.path.join(current_dir, "groceries.sqlite3")
db = SQLAlchemy()
db.init_app(app)
app.app_context().push()

class Admin(db.Model):
    __tablename__='admin'
    admin_id=db.Column(db.String, primary_key=True, autoincrement=True)
    adminpass=db.Column(db.String, nullable=False)
    adminname=db.Column(db.String, nullable=False)
    adminemail=db.Column(db.String, unique=True, nullable=False)
    
class User(db.Model):
    __tablename__='user'
    user_id=db.Column(db.String, primary_key=True, autoincrement=True)
    userpass=db.Column(db.String, nullable=False)
    user_name=db.Column(db.String, nullable=False)
    user_email=db.Column(db.String, unique=True, nullable=False)
    wallet=db.Column(db.Integer)
    
class Category(db.Model):
    __tablename__='category'
    cid=db.Column(db.Integer, primary_key=True, autoincrement=True)
    cname=db.Column(db.String, nullable=False)

class Product(db.Model):
    __tablename__='product'
    pid=db.Column(db.Integer, primary_key=True, autoincrement=True)
    pname=db.Column(db.String, nullable=False)
    manu=db.Column(db.String, nullable=False)
    cid=db.Column(db.Integer, db.ForeignKey("category.cid"), nullable=False)
    cname=db.Column(db.String, nullable=False)
    rate=db.Column(db.String)
    added=db.Column(db.Date, nullable=False)
    quantity=db.Column(db.Integer)
    exp=db.Column(db.Date)
    pimg = db.Column(db.LargeBinary)
    unit=db.Column(db.String)
    
class Cart(db.Model):
    __tablename__='cart'
    cartnum=db.Column(db.Integer, primary_key=True, autoincrement=True)
    pid=db.Column(db.Integer, db.ForeignKey("product.pid"), nullable=False)
    user_id=db.Column(db.String, db.ForeignKey("user.user_id"), nullable=False)
    quantity=db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='cart', foreign_keys=[pid])


'''class Purchases(db.Model):
    __tablename__='purchases'
    pid=db.Column(db.Integer, db.ForeignKey("product.pid"), nullable=False)
    user_id=db.Column(db.String, db.ForeignKey("user.user_id"), nullable=False)
    quantity=db.Column(db.Integer, nullable=False)
    cost=db.Column(db.Numeric, nullable=False)
    puron=db.Column(db.DateTime, nullable=False)
    '''
    
@app.route("/", methods=['GET'])
def home():
    if request.method=='GET':
        return render_template("home.html")

@app.route("/adminlogin", methods=["POST", "GET"])
def adminlogin():
    if request.method=="GET":
        return render_template("adminlogin.html")
    if request.method=="POST":
        engine=create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        admins=Table('admin', metadata,
                    Column('admin_id', String, primary_key=True),
                    Column('adminpass',String),
                    Column('adminname',String),
                    Column('adminemail',String),
        )
        admin_id=request.form["admin_id"]
        adminpass=request.form["adminpass"]
        admin=Admin.query.filter_by(admin_id=admin_id).first()
        if not admin:
            return render_template("wrongadmin.html")
        else:
            pwd=admin.adminpass
            if pwd!=adminpass:
                return render_template("wrap.html")
            else:
                return redirect(url_for('admin_home', admin_id=admin_id))
            
@app.route("/adminsignup", methods=["GET", "POST"])
def adminsignup():
    if request.method=="GET":
        return render_template("adminsignup.html")
    if request.method=="POST":
        engine=create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        admins=Table('admin', metadata,
                    Column('admin_id', String, primary_key=True),
                    Column('adminpass',String),
                    Column('adminname',String),
                    Column('adminemail',String),
        )
        admin_id=request.form["admin_id"]
        adminpass=request.form["adminpass"]
        adminname=request.form["adminname"]
        adminemail=request.form["adminemail"]
        admin=Admin.query.filter(or_(Admin.admin_id == admin_id, Admin.adminemail == adminemail)).all()
        if not admin:
            newadmin=admins.insert().values(
                admin_id=admin_id,
                adminpass=adminpass,
                adminname=adminname,
                adminemail=adminemail,
            )
            session.execute(newadmin)
            session.commit()
            return redirect(url_for('admin_home', admin_id=admin_id))
        else:
            return render_template("adminexists.html")
        

@app.route("/adminhome/<admin_id>", methods=["GET","POST"])
def admin_home(admin_id):
    if request.method=="GET":
        categories=Category.query.all()
        products=Product.query.all()
        for product in products:
            if product.pimg is not None:
                product.pimg = base64.b64encode(product.pimg).decode('utf-8')
        return render_template("adminhome.html", admin_id=admin_id, products=products, categories=categories)


@app.route("/addcategory/<admin_id>", methods=["GET","POST"])
def addcategory(admin_id):
    if request.method=="GET":
        return render_template("addcategory.html", admin_id=admin_id)
    if request.method=="POST":
        engine = create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        category = Table('category', metadata,
            Column('cid', Integer, primary_key=True),
            Column('cname', String)
        )
        cname=request.form["cname"]
        new=category.insert().values(
            cname=cname
        )
        session.execute(new)
        session.commit()
        return redirect(url_for('admin_home', admin_id=admin_id))

@app.route("/adminhome/<admin_id>/updatecat/<cid>", methods=["GET","POST"])
def updatecat(cid,admin_id):
    category=Category.query.filter_by(cid=cid).first()
    if request.method=="GET":
        return render_template("updatecat.html", category=category, admin_id=admin_id)
    elif request.method=="POST":
        cat=category
        engine = create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        category = Table('category', metadata,
            Column('cid', Integer, primary_key=True),
            Column('cname', String)
        )
        cname=request.form["cname"]
        cat.cname=cname
        db.session.commit()
        return redirect(url_for('admin_home', admin_id=admin_id))

@app.route("/adminhome/<admin_id>/deletecat/<cid>", methods=["GET","POST"])
def deletecat(cid,admin_id):
    admin=Admin.query.filter_by(admin_id=admin_id).first()
    if request.method=="GET":
        return render_template("deletecat.html", cid=cid, admin_id=admin_id)
    if request.method=="POST":
        adminpass=request.form["adminpass"]
        pwd=admin.adminpass
        if pwd!=adminpass:
            return render_template("wrdp2.html", admin_id=admin_id, cid=cid)
        else:
            products=Product.query.filter_by(cid=cid).all()
            for product in products:
                db.session.delete(product)
            db.session.commit()
            category=Category.query.filter_by(cid=cid).first()
            db.session.delete(category)
            db.session.commit()
            return redirect(url_for('admin_home', admin_id=admin_id))
        
@app.route("/adminhome/<admin_id>/addproduct", methods=["GET","POST"])
def addproduct(admin_id):
    if request.method=="GET":
        categories=Category.query.all()
        return render_template("addproduct.html", admin_id=admin_id,categories=categories)
    elif request.method=="POST":
        engine = create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        product = Table('product', metadata,
            Column('pid', Integer, primary_key=True),
            Column('pname', String),
            Column('manu', String),
            Column('cid', Integer),
            Column('cname', String),
            Column('rate', String),
            Column('added', Date),
            Column('quantity', Integer),
            Column('exp', Date),
            Column('pimg', LargeBinary),
            Column('unit', String)
        )
        
        pname=request.form["pname"]
        manu=request.form["manu"]
        cid=request.form["cid"]
        category=Category.query.filter_by(cid=cid).first()
        cname=category.cname
        rate=request.form["rate"]
        added= date.fromisoformat(request.form['added'])
        quantity=request.form["quantity"]
        exp=date.fromisoformat(request.form['exp'])
        uploaded_image = request.files['pimg']
        pimg_data = BytesIO(uploaded_image.read())
        unit=request.form['unit']
        new=product.insert().values(
            pname=pname,
            manu=manu,
            cid=cid,
            cname=cname,
            rate=rate,
            added=added,
            quantity=quantity,
            exp=exp,
            pimg=pimg_data.read(),
            unit=unit
        )
        session.execute(new)
        session.commit()
        return redirect(url_for('admin_home', admin_id=admin_id))

@app.route("/adminhome/<admin_id>/updatepro/<pid>", methods=["GET","POST"])
def updatepro(pid, admin_id):
    product=Product.query.filter_by(pid=pid).first()
    
    categories=Category.query.all()
    if request.method=="GET":
        return render_template("updatepro.html", product=product, admin_id=admin_id, categories=categories)    
    elif request.method=="POST":
        pro=product
        uploaded_image = request.files['pimg']
        engine = create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        product = Table('product', metadata,
            Column('pid', Integer, primary_key=True),
            Column('pname', String),
            Column('manu', String),
            Column('cid', Integer),
            Column('cname', String),
            Column('rate', String),
            Column('added', Date),
            Column('quantity', Integer),
            Column('exp', Date),
            Column('pimg', LargeBinary),
            Column('unit', String)
        )
        pname=request.form["pname"]
        manu=request.form["manu"]
        cid=request.form["cid"]
        category=Category.query.filter_by(cid=cid).first()
        cname=category.cname
        rate=request.form["rate"]
        added=date.fromisoformat(request.form['added'])        
        quantity=request.form["quantity"]
        exp=date.fromisoformat(request.form['exp'])
        unit=request.form['unit']
        if uploaded_image:  
            pimg_data = BytesIO(uploaded_image.read())
            pro.pimg = pimg_data.read() 
        
        pro.pname=pname
        pro.manu=manu
        pro.cid=cid
        pro.cname=cname
        pro.rate=rate
        pro.added=added
        pro.quantity=quantity
        pro.exp=exp
        pro.unit=unit
        db.session.commit()
        return redirect(url_for('admin_home', admin_id=admin_id))

@app.route("/adminhome/<admin_id>/deletepro/<pid>", methods=["GET","POST"])
def deletepro(pid, admin_id):
    admin=Admin.query.filter_by(admin_id=admin_id).first()
    if request.method=="GET":
        return render_template("deletepro.html", pid=pid, admin_id=admin_id)
    if request.method=="POST":
        adminpass=request.form["adminpass"]
        pwd=admin.adminpass
        if pwd!=adminpass:
            return render_template("wrdp.html", admin_id=admin_id, pid=pid)
        else:
            product=Product.query.filter_by(pid=pid).first()
            carts=Cart.query.filter_by(pid=pid).all()
            db.session.delete(product)
            for cart in carts:
                db.session.delete(cart)
            db.session.commit()
            return redirect(url_for('admin_home', admin_id=admin_id))


@app.route("/usersignup", methods=["GET", "POST"])
def usersignup():
    if request.method=="GET":
        return render_template("usersignup.html")
    if request.method=="POST":
        engine=create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        users=Table('user', metadata,
                    Column('user_id', String, primary_key=True),
                    Column('userpass',String),
                    Column('user_name',String),
                    Column('user_email',String),
                    Column('wallet', Integer)
                    
        )
        user_id=request.form["user_id"]
        userpass=request.form["userpass"]
        user_name=request.form["user_name"]
        user_email=request.form["user_email"]
        wallet=0
        
        user=User.query.filter(or_(User.user_id == user_id, User.user_email == user_email)).all()
        if not user:
            newuser=users.insert().values(
                user_id=user_id,
                userpass=userpass,
                user_name=user_name,
                user_email=user_email,
                wallet=wallet
            )
            session.execute(newuser)
            session.commit()
            return redirect(url_for('user_home', user_id=user_id))
            
        else:
            return render_template("userexists.html")
        
@app.route("/userlogin", methods=["POST", "GET"])
def userlogin():
    if request.method=="GET":
        return render_template("userlogin.html")
    if request.method=="POST":
        engine=create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        users=Table('user', metadata,
                    Column('user_id', String, primary_key=True),
                    Column('userpass',String),
                    Column('user_name',String),
                    Column('user_email',String),
                    Column('wallet', Integer)
        )
        user_id=request.form["user_id"]
        userpass=request.form["userpass"]
        user=User.query.filter_by(user_id=user_id).first()
        if not user:
            return render_template("wronguser.html")
        else:
            pwd=user.userpass
            if pwd!=userpass:
                return render_template("wrup.html")
            else:
                return redirect(url_for('user_home', user_id=user_id))



'''@app.route('/userhome/<user_id>/sort/<sort_by>', methods=['GET', 'POST'])
def user_home_sort(user_id, sort_by):
    products = Product.query.order_by(getattr(Product, sort_by)).all()
    return render_template('userhome.html', user_id=user_id, products=products)'''

@app.route('/userhome/<user_id>/search', methods=['GET'])
def user_home_search(user_id):
    search_query = request.args.get('search_query')
    products = Product.query.filter(Product.pname.ilike(f'%{search_query}%')).all()
    for product in products:
            if product.pimg is not None:
                product.pimg = base64.b64encode(product.pimg).decode('utf-8')
    return render_template('userhome.html', user_id=user_id, products=products)

@app.route('/userhome/<user_id>/sort_filter', methods=['GET'])
def user_home_sort_filter(user_id):
    sort_by = request.args.get('sort_attribute')
    category = request.args.get('category')
    categories = db.session.query(Product.cname).distinct().all()

    if category == 'all':
        products = Product.query.order_by(getattr(Product, sort_by)).all()
        for product in products:
            if product.pimg is not None:
                product.pimg = base64.b64encode(product.pimg).decode('utf-8')
    else:
        products = Product.query.filter_by(cname=category).order_by(getattr(Product, sort_by)).all()
        for product in products:
            if product.pimg is not None:
                product.pimg = base64.b64encode(product.pimg).decode('utf-8')
    return render_template('userhome.html', user_id=user_id, products=products, categories=categories)

@app.route("/userhome/<user_id>", methods=["GET"])
def user_home(user_id):
    if request.method=="GET":
        categories = db.session.query(Product.cname).distinct().all()
        products = Product.query.order_by(desc(Product.added)).all()
        for product in products:
            if product.pimg is not None:
                product.pimg = base64.b64encode(product.pimg).decode('utf-8')
        return render_template("userhome.html", user_id=user_id, products=products, categories=categories)

@app.route("/userhome/<user_id>/cart/<pid>", methods=["GET", "POST"])
def addtocart(user_id, pid):
    if request.method=="GET":
        product=Product.query.filter_by(pid=pid).first()
        if product.quantity==0:
            return render_template("nostock.html", user_id=user_id, pid=pid)
        else:
            return render_template("addtocart.html", user_id=user_id, pid=pid, product=product)
    if request.method=="POST":
        engine = create_engine('sqlite:///groceries.sqlite3', echo=True)
        Session = sessionmaker(bind=engine)
        session = Session()
        metadata = MetaData()
        cart = Table('cart', metadata,
            Column('cartnum', Integer, primary_key=True),
            Column('pid', Integer),
            Column('user_id', String),
            Column('quantity', Integer)
        )
        quantity=int(request.form["quantity"])
        
        new=cart.insert().values(
            pid=pid,
            user_id=user_id,
            quantity=quantity
        )
        session.execute(new)
        session.commit()
        product=Product.query.filter_by(pid=pid).first()
        product.quantity=product.quantity-quantity
        db.session.commit()
        return redirect(url_for('user_home', user_id=user_id))
    
@app.route("/userhome/<user_id>/gotocart", methods=["GET", "POST"])
def gotocart(user_id):
    if request.method=="GET":
        cart_items=Cart.query.filter_by(user_id=user_id).all()
        cost=0
        cart_details = []
        for item in cart_items:
            product = item.product
            pimg_data = product.pimg
            if pimg_data is not None:
                pimg_base64 = base64.b64encode(pimg_data).decode('utf-8')
            else:
                pimg_base64 = None
            cart_details.append({
                'cartnum': item.cartnum,
                'user_id': item.user_id,
                'pid': item.pid,
                'quantity': item.quantity,
                'pname': product.pname,
                'cname': product.cname,
                'manu': product.manu,
                'rate': product.rate,
                'added': product.added,
                'exp': product.exp,
                'pimg':product.pimg,
                'product_quantity': product.quantity,
                'pimg': pimg_base64,
                'unit': product.unit
            })
        
            
        for product in cart_details:
            x=int(product['rate'])*int(product['quantity'])
            cost=cost+x
        user=User.query.filter_by(user_id=user_id).first()
        wallet=user.wallet
        return render_template("gotocart.html", user_id=user_id, cart_details=cart_details, cost=cost, wallet=wallet)
    
@app.route('/userhome/<user_id>/gotocart/change/<cartnum>', methods=["GET", "POST"])
def updatecart(user_id, cartnum):
    odr=Cart.query.filter_by(cartnum=cartnum).first()
    prod=odr.product
    if request.method=="GET":
        pname=prod.pname
        left=prod.quantity+odr.quantity
        return render_template("updatecart.html", user_id=user_id, odr=odr, pname=pname, cartnum=cartnum, left=left)
    
    if request.method=="POST":
        change=int(request.form['quantity'])
        prod.quantity=prod.quantity+odr.quantity-change
        odr.quantity=change
        db.session.commit()
        return redirect(url_for('gotocart', user_id=user_id))

@app.route("/userhome/<user_id>/gotocart/remove/<cartnum>", methods=["GET","POST"])
def removecart(user_id, cartnum):
    if request.method=="GET":
        cart=Cart.query.filter_by(cartnum=cartnum).first()
        product=cart.product
        product.quantity+=cart.quantity
        db.session.delete(cart)
        db.session.commit()
        return redirect(url_for('gotocart', user_id=user_id))
@app.route("/userhome/<user_id>/wallet", methods=["GET", "POST"])
def wallet(user_id):
    if request.method=='GET':
        user=User.query.filter_by(user_id=user_id).first()
        return render_template('wallet.html', user=user, user_id=user_id)

@app.route("/userhome/<user_id>/wallet/add", methods=["GET", "POST"])
def addmoney(user_id):
    user=User.query.filter_by(user_id=user_id).first()
    if request.method=='GET':
        return render_template('addmoney.html', user=user, user_id=user_id)
    if request.method=='POST':
        wallet=request.form['wallet']
        userpass=request.form['userpass']
        if user.userpass!=userpass:
            return render_template('wrmp.html', user=user, user_id=user_id)
        else:
            user.wallet=user.wallet + int(wallet)
            db.session.commit()
            return redirect(url_for('wallet', user_id=user_id))

if __name__=="__main__":
    app.run(
        debug=True
    )


