# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db, DataValidationError
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    # ADD YOUR TEST CASES HERE
    def test_read_a_product(self):
        """it should get product by it's id from the database"""
        product = ProductFactory()
        product.id = None
        product.create()
        app.logger.info(f'product created  Product: {product.name}')
        self.assertIsNotNone(product.id)
        product_from_db = Product.find(product.id)
        self.assertEqual(product_from_db.id, product.id)
        self.assertEqual(product_from_db.name, product.name)
        self.assertEqual(product_from_db.description, product.description)
        self.assertEqual(product_from_db.price, product.price)
        self.assertEqual(product_from_db.available, product.available)
        self.assertEqual(product_from_db.category, product.category)

    def test_update_a_product(self):
        """Test update product details"""
        product = ProductFactory()
        app.logger.info(f'Product: {product} initiated')
        product.id = None
        product.create()
        app.logger.info(f'Product: {product} created')
        original_id = product.id
        product.description = "updated description"
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "updated description")
        found = Product.all()
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].id, original_id)
        self.assertEqual(found[0].description, "updated description")

    def test_update_a_product_with_no_id__should_raise_data_validation_error(self):
        """Test update product details failure as id is None"""
        product = ProductFactory()
        app.logger.info(f'Product: {product} initiated')
        product.id = None
        product.create()
        app.logger.info(f'Product: {product} created')
        product.id = None
        product.description = "updated description"
        with self.assertRaises(DataValidationError):
            product.update()

    def test_delete_product(self):
        """Test delete product from the database"""
        product = ProductFactory()
        product.id = None
        product.create()
        self.assertEqual(len(Product.all()), 1)
        product.delete()
        self.assertEqual(len(Product.all()), 0)

    def test_list_all_products(self):
        """Test Listing all products from the database"""
        products = Product.all()
        self.assertEqual(products, [])
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
        products = Product.all()
        self.assertEqual(len(products), 5)

    def test_find_product_by_name(self):
        """Test finding product in the database by it's name"""
        products = []
        for _ in range(5):
            product = ProductFactory()
            product.id = None
            product.create()
            products.append(product)
        first_product_name = products[0].name
        number_of_first_name_occurance = len([x for x in products if x.name == first_product_name])
        products_from_db = Product.find_by_name(first_product_name)
        self.assertEqual(number_of_first_name_occurance, len([products_from_db]))

    def test_find_by_availability(self):
        """Test find product by it's availability"""
        products = []
        for _ in range(10):
            product = ProductFactory()
            product.id = None
            product.create()
            products.append(product)
        first_product_availability = products[0].available
        count = len([x for x in products if x.available == first_product_availability])
        products_from_db = Product.find_by_availability(first_product_availability)
        self.assertEqual(products_from_db.count(), count)
        for product in products_from_db:
            self.assertEqual(product.available, first_product_availability)

    def test_find_by_category(self):
        """Test finding product from database by category"""
        products = ProductFactory.create_batch(10)
        for product in products:
            product.create()
        category = products[0].category
        count = len([product for product in products if product.category == category])
        found = Product.find_by_category(category)
        self.assertEqual(found.count(), count)
        for product in found:
            self.assertEqual(product.category, category)

    def test_find_py_price(self):
        """Test get product by price from database"""
        product = ProductFactory()
        product.id = None
        product.price = "10"
        product.create()

        # self.assertEqual(Product.all()[0].price, product)
        found = Product.find_by_price("10")
        self.assertEqual(found[0].name, product.name)
        self.assertEqual(found[0].description, product.description)
        self.assertEqual(found[0].available, product.available)
        self.assertEqual(found[0].category, product.category)
        self.assertEqual(found[0].price, 10)

    def test_product_deserialize_with_missing_args(self):
        """Test deserialize a product without a name"""

        with self.assertRaises(DataValidationError):
            product = ProductFactory()
            product.deserialize(data={
                    "description": "product without a name",
                    "available": False,
                    "category": "invalid category",
                    "price": "$10"
                }
            )

    def test_product_deserialize_with_invalid_available_data_type(self):
        """Test deserialize a product with available as string not bool"""

        with self.assertRaises(DataValidationError):
            product = ProductFactory()
            product.deserialize(data={
                    "description": "product without a name",
                    "available": "False",
                    "category": "CLOTHS",
                    "price": "10",
                    "name": "product with invalid availability value"
                }
            )

    def test_product_deserialize_with_null_data_object(self):
        """Test deserialize a product without data object"""

        with self.assertRaises(DataValidationError):
            product = ProductFactory()
            product.deserialize(data=None)

    def test_product_deserialize_with_category(self):
        """Test deserialize a product with invalid category"""

        with self.assertRaises(DataValidationError):
            product = ProductFactory()
            product.deserialize(data={
                    "description": "product without a name",
                    "available": False,
                    "category": "invalid category",
                    "price": "10",
                    "name": "product with invalid category"
                }
            )
