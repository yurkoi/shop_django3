import sys
from io import BytesIO

from PIL import Image

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse


#***************
#1 Category
#2 Product
#3 CartProduct
#4 Cart
#5 Order
#***************
#6 Order
#7 Specification

User = get_user_model()


def get_models_for_count(*model_names):
    return [models.Count(model_name) for model_name in model_names]


def get_product_url(obj, viewname):
    ct_model = obj.__class__._meta.model_name
    return reverse(viewname, kwargs={'ct_model': ct_model, 'slug': obj.slug})


class MinResolutionErrorExeption(Exception):
    pass


class MaxResolutionErrorExeption(Exception):
    pass


class LatestProductsManager:

    @staticmethod
    def get_products_for_main_page(*args, **kwargs):
        with_respect_to = kwargs.get('with_respect_to')
        products = []
        ct_models = ContentType.objects.filter(model__in=args)
        for ct_model in ct_models:
            model_products = ct_model.model_class()._base_manager.all().order_by('-id')[:5]
            products.extend(model_products)
        if with_respect_to:
            ct_model = ContentType.objects.filter(model=with_respect_to)
            if ct_model.exists():
                if with_respect_to in args:
                    return sorted(products, key=lambda x:
                    x.__class__._meta.model_name.startswith(with_respect_to), reverse=True)
        return products


class LatestProducts:

    objects = LatestProductsManager()


class CategoryManager(models.Manager):

    CATEGORY_NAME_COUNT_NAME = {
        'Notebooks': 'notebook__count',
        'Smartphones': 'smartphone__count'
    }

    def get_queryset(self):
        return super().get_queryset()

    def get_categories_for_lef_sidebar(self):
        models = get_models_for_count('notebook', 'smartphone')
        qs = list(self.get_queryset().annotate(*models))
        data = [
            dict(name=c.name, url=c.get_absolute_url(),
                 count=getattr(c, self.CATEGORY_NAME_COUNT_NAME[c.name]))
            for c in qs
        ]
        return data


class Category(models.Model):

    name = models.CharField(max_length=255, verbose_name='name of category')
    slug = models.SlugField(unique=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})


class Product(models.Model):

    MAX_IMAGE_SIZE = 3145728
    MIN_RESOLUTION = (400, 400)
    MAX_RESOLUTION = (1000, 1000)

    class Meta:
        abstract = True

    category = models.ForeignKey(Category, verbose_name='category', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name='product name')
    slug = models.SlugField(unique=True)
    image = models.ImageField(verbose_name='image')
    descriptions = models.TextField(verbose_name='description', null=True)
    price = models.DecimalField(max_digits=9, decimal_places=3, verbose_name='price')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        image = self.image
        img = Image.open(image)
        min_height, min_width = Product.MIN_RESOLUTION
        max_height, max_width = Product.MAX_RESOLUTION
        if img.height < min_height or img.width < min_width:
            raise MinResolutionErrorExeption('Resolution of image less than minimum!')
        if img.height > max_height or img.width > max_width:
            new_img = img.convert('RGB')
            resized_new_img = new_img.resize(self.MIN_RESOLUTION, Image.ANTIALIAS)
            filestream = BytesIO()
            resized_new_img.save(filestream, 'JPEG', quality=90)
            filestream.seek(0)
            name = '{}.{}'.format(*self.image.name.split('.'))
            self.image = InMemoryUploadedFile(
                filestream, 'ImageField', name, 'jpeg/image', sys.getsizeof(filestream), None
            )
            super().save(*args, **kwargs)
        super().save(*args, **kwargs)


class Notebook(Product):

    diagonal = models.CharField(max_length=255, verbose_name='Diagonal')
    display = models.CharField(max_length=255, verbose_name='display type')
    processor_freq = models.CharField(max_length=255, verbose_name='processor frequency')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    video = models.CharField(max_length=255, verbose_name='videocard')
    time_without_charge = models.CharField(max_length=255, verbose_name='working time for battery')

    def __str__(self):
        # return '{} : {}'.format(self.category.name, self.title)
        return 'Notebook {}'.format(self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')

    def get_query_set(self):
        return Smartphone.objects.all().select_related('category')


class Smartphone(Product):
    diagonal = models.CharField(max_length=255, verbose_name='Diagonal')
    display = models.CharField(max_length=255, verbose_name='display type')
    resolution = models.CharField(max_length=255, verbose_name='resolution')
    accum_volume = models.CharField(max_length=255, verbose_name='battery volume')
    ram = models.CharField(max_length=255, verbose_name='RAM')
    sd = models.BooleanField(default=True, verbose_name='Cart exists?')
    sd_volume = models.CharField(
        max_length=255, null=True, blank=True, verbose_name='Max capacity of sd'
    )
    main_cam_mp = models.CharField(max_length=255, verbose_name='main camera')
    frontal_cam_mp = models.CharField(max_length=255, verbose_name='frontal camera')

    def __str__(self):
        return 'Smartphone : {}'.format(self.title)

    def get_absolute_url(self):
        return get_product_url(self, 'product_detail')

    # def get_queryset(self):
    #     return Smartphone.objects.all().select_related('category')


class CartProduct(models.Model):

    user = models.ForeignKey('Customer', verbose_name='customer', on_delete=models.CASCADE)
    cart = models.ForeignKey("cart", verbose_name='cart', on_delete=models.CASCADE,
                             related_name='related_products')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", 'object_id')
    qty = models.PositiveIntegerField(default=1)
    final_price = models.DecimalField(max_digits=9, decimal_places=3, verbose_name='final price')

    def __str__(self):
        return f'Cart product {self.content_object.title}'


class Cart(models.Model):

    owner = models.ForeignKey('Customer', verbose_name='owner', on_delete=models.CASCADE)
    products = models.ManyToManyField(CartProduct, blank=True, related_name='related_cart')
    total_products = models.PositiveIntegerField(default=0)
    final_price = models.DecimalField(max_digits=9, decimal_places=3, verbose_name='final price')
    in_order = models.BooleanField(default=False)
    for_anonymous_user = models.BooleanField(default=False)

    def __str__(self):
        return str(self.id)


class Customer(models.Model):

    user = models.ForeignKey(User, verbose_name='user', on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, verbose_name='phone number')
    address = models.CharField(max_length=255, verbose_name='address')

    def __str__(self):
        return f'Customer: {self.user.first_name} {self.user.last_name}'
