from decimal import ROUND_UP
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, DecimalField, PasswordField
from wtforms.validators import DataRequired


class HomeForm(FlaskForm):
    item_name = StringField("Item Name", validators=[DataRequired()])
    bulk_cost = DecimalField("Cost Per Case", places=2, rounding=ROUND_UP, validators=[DataRequired()])
    bulk_weight = DecimalField("Item Bulk Weight In Pounds", places=2, rounding=ROUND_UP, validators=[DataRequired()])
    submit = SubmitField("Get cost per ounce")


class CreateDish(FlaskForm):
    dish_name = StringField("Name Of Dish", validators=[DataRequired()])
    ingredient_name = StringField("Name Of Item To Add", validators=[DataRequired()])
    serving_size = DecimalField("Serving Size", places=2, rounding=ROUND_UP,  validators=[DataRequired()])
    submit = SubmitField("Add Item To Dish")


class CheckPortionSize(FlaskForm):
    name = StringField("Name Of Item", validators=[DataRequired()])
    portion_size = DecimalField("Portion size in Ounces")
    submit = SubmitField("Get Food Cost")


class MenuPrices(FlaskForm):
    name = StringField("Name Of Menu Item", validators=[DataRequired()])
    submit = SubmitField("Get Dish Numbers")


class RecipeForm(FlaskForm):
    name = StringField("Name Of Menu Item", validators=[DataRequired()])
    submit = SubmitField("Get Recipe")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Submit")


class RegisterForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")






