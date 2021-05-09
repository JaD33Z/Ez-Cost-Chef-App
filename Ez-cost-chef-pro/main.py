from flask import Flask, render_template, flash, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from forms import HomeForm, CheckPortionSize, CreateDish, MenuPrices, RecipeForm, LoginForm, RegisterForm
from sqlalchemy import func
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chef.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login = LoginManager(app)
admin = Admin(app)

######### DATABASE MODELS ################################

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String)


class FoodItem(db.Model):
    __tablename__ = "food_item"
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String, nullable=False)
    item_cost_oz = db.Column(db.Numeric, nullable=False)


class MenuDish(db.Model):
    __tablename__ = "menu_dish"
    id = db.Column(db.Integer, primary_key=True)
    dish_name = db.Column(db.String, nullable=False)
    ingredient_name = db.Column(db.String, nullable=False)
    serving_size = db.Column(db.Numeric, nullable=False)
    portion_cost = db.Column(db.Numeric, nullable=False)


class MenuNumbers(db.Model):
    __tablename__ = "menu_numbers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    food_cost = db.Column(db.Numeric, nullable=False)
    menu_price = db.Column(db.Numeric, nullable=False)


db.create_all()

########### ADMIN PAGE MODEL VIEWS FOR DATABASE ###########################

class MyModelView(ModelView):
    def is_accessible(self):
        if current_user.id == 1:
            return True
        else:
            return False


admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(FoodItem, db.session))
admin.add_view(MyModelView(MenuDish, db.session))
admin.add_view(MyModelView(MenuNumbers, db.session))

####### USER LOGIN ROUTES ###################################

@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/register', methods=["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, please log in.")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            password=hash_and_salted_password,
            name=form.name.data
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('login'))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email doesn't exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password is incorrect, please try again.")
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template("login.html", form=form, current_user=current_user)


@app.route('/logout', methods=["GET", "POST"])
def log_out():
    logout_user()
    return redirect(url_for('home'))


######### MAIN APP PAGE ROUTES #########################################

## Adds item to inventory and calculates cost of item per ounce,
## according to items price per case.

@app.route('/', methods=["GET", "POST"])
def home():
    form = HomeForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("Only registered users may enter new items to inventory. "
                  "Visitors are welcome to experiment with "
                  "pre-existing items on all other pages. "
                  "Find item names in Dropdown box links.")
            return redirect(url_for('home'))
        bulk_cost = form.bulk_cost.data
        bulk_weight = form.bulk_weight.data
        food_cost = bulk_cost / (bulk_weight * 16)
        new_item = FoodItem(
            item_name=form.item_name.data,
            item_cost_oz=f"{food_cost:.2f}",
        )
        db.session.add(new_item)
        db.session.commit()
        results = f"{new_item.item_name} costs ${food_cost:.2f} per oz."
        return redirect(url_for('food_cost_per_oz', results=results))
    return render_template('index.html', form=form)


## Results page shows results for: home, get_portion_size, and get_menu_numbers functions.

@app.route('/food_cost/<results>', methods=["GET","POST"])
def food_cost_per_oz(results):
    return render_template('food_cost.html', results=results)


## Get exact food cost for individual item's potential serving size,
## also calculates what you should charge for that serving size.
## Intended for building a dish to serve on the menu and forecast profit/cost.

@app.route('/portion.html', methods=["GET","POST"])
def get_portion_size():
    form = CheckPortionSize()
    if form.validate_on_submit():
        name = form.name.data
        portion_size = form.portion_size.data
        item_id = FoodItem.query.filter_by(item_name=form.name.data).first()
        if item_id:
            item_cost = item_id.item_cost_oz
            portion_cost = portion_size * item_cost
            menu_price = float(portion_cost) / .30
            results = f"Food cost of {name} will be \n"\
                      f"${portion_cost:.2f} \n" \
                      f"Suggested selling price is ${menu_price:.2f} \n" \
                      f"for this portion size."
            return redirect(url_for('food_cost_per_oz', results=results))
        else:
            flash("That item is not currently in the system!")
    return render_template('portion.html', form=form)


## Build a dish to put on the menu, item by item with individual portion size.
## Cost Pro app stores your dish name, along with it's ingredients
## and their measures in the database.

@app.route('/dish.html', methods=["GET","POST"])
def create_dish():
    form = CreateDish()
    if form.validate_on_submit():
        item_id = FoodItem.query.filter_by(item_name=form.ingredient_name.data).first()
        if item_id:
            item_cost = item_id.item_cost_oz
            portion_cost = form.serving_size.data * item_cost
            new_dish = MenuDish(
                dish_name=form.dish_name.data,
                ingredient_name=form.ingredient_name.data,
                serving_size=form.serving_size.data,
                portion_cost=portion_cost,
            )
            db.session.add(new_dish)
            db.session.commit()
            return redirect(url_for('create_dish'))
        else:
            flash("That item is not currently in the system, add item to inventory first!")
            return redirect(url_for('create_dish'))
    return render_template('dish.html', form=form)


## Stores your created dish into database, returns the total food cost
## and suggested menu selling price for your completed dish.

@app.route('/get_numbers.html', methods=["GET","POST"])
def get_menu_numbers():
    form = MenuPrices()
    if form.validate_on_submit():
        qry_cost = MenuDish.query.with_entities\
            (func.sum(MenuDish.portion_cost))\
            .filter_by(dish_name=form.name.data).all()
        total_cost = qry_cost[0][0]
        if total_cost is None:
            flash("That dish has not been created yet!")
        else:
            menu_price = float(total_cost) / .30
            menu_price = f"{menu_price:.2f}"
            total_cost = f"{total_cost:.2f}"
            new_numbers = MenuNumbers(
                name=form.name.data,
                food_cost=total_cost,
                menu_price=menu_price,
            )
            db.session.query(MenuNumbers.name).filter_by(name=new_numbers.name).delete()
            db.session.add(new_numbers)
            db.session.commit()
            results = f"Total food cost for this dish is ${total_cost} \n" \
                      f"Suggested menu selling price is ${menu_price}"
            return redirect(url_for('food_cost_per_oz', results=results))
    return render_template('get_numbers.html', form=form)


####### DROP-DOWN BOX APP ROUTES ###################

## Queries and returns a list of all completed dishes on the menu
## along with their menu price.

@app.route('/data_content.html')
def menu_items():
    search_res = MenuNumbers.query.with_entities(MenuNumbers.name,MenuNumbers.menu_price).all()
    names = [i[0] for i in search_res]
    nums = [float(i[1]) for i in search_res]
    contents = zip(names, nums)
    return render_template('data_content.html', contents=contents)


## Returns a list of all items in the inventory and the item's cost per ounce.

@app.route('/inventory.html')
def inventory_items():
    search_res = FoodItem.query.with_entities(FoodItem.item_name, FoodItem.item_cost_oz).all()
    names = [i[0] for i in search_res]
    nums = [float(i[1]) for i in search_res]
    contents = zip(names, nums)
    print(contents)
    return render_template('inventory.html', contents=contents)

## Search for dish name and returns all of it's ingredients.

@app.route('/recipes.html', methods=["GET","POST"])
def get_recipes():
    form = RecipeForm()
    if form.validate_on_submit():
        name = form.name.data
        contents = [r.ingredient_name for r in db.session.query(MenuDish.ingredient_name).filter_by(dish_name=name).distinct()]
        if not contents:
            flash("That item is not in the inventory!")
            return render_template('recipes.html', form=form)
        results = f"{name}"
        return render_template('recipe_results.html', contents=contents, results=results)
    return render_template('recipes.html', form=form)




if __name__ == '__main__':
    app.run(debug=False)
