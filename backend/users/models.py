from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

GST_STATE_CODE = (
    ("1", "JAMMU AND KASHMIR"),
    ("2", "HIMACHAL PRADESH"),
    ("3", "PUNJAB"),
    ("4", "CHANDIGARH"),
    ("5", "UTTARAKHAND"),
    ("6", "HARYANA"),
    ("7", "DELHI"),
    ("8", "RAJASTHAN"),
    ("9", "UTTAR PRADESH"),
    ("10", "BIHAR"),
    ("11", "SIKKIM"),
    ("12", "ARUNACHAL PRADESH"),
    ("13", "NAGALAND"),
    ("14", "MANIPUR"),
    ("15", "MIZORAM"),
    ("16", "TRIPURA"),
    ("17", "MEGHLAYA"),
    ("18", "ASSAM"),
    ("19", "WEST BENGAL"),
    ("20", "JHARKHAND"),
    ("21", "ODISHA"),
    ("22", "CHATTISGARH"),
    ("23", "MADHYA PRADESH"),
    ("24", "GUJARAT"),
    ("25", "DAMAN AND DIU"),
    ("26", "DADRA AND NAGAR HAVELI"),
    ("27", "MAHARASHTRA"),
    ("28", "ANDHRA PRADESH(BEFORE DIVISION)"),
    ("29", "KARNATAKA"),
    ("30", "GOA"),
    ("31", "LAKSHWADEEP"),
    ("32", "KERALA"),
    ("33", "TAMIL NADU"),
    ("34", "PUDUCHERRY"),
    ("35", "ANDAMAN AND NICOBAR ISLANDS"),
    ("36", "TELANGANA"),
    ("37", "ANDHRA PRADESH (NEW)"),
)


class TimeStampModel(models.Model):
    class Meta:
        abstract = True

    cdate = models.DateTimeField(auto_now_add=True)
    udate = models.DateTimeField(auto_now=True)


# class MyAccountManager(BaseUserManager):
#     def create_user(self, **kwargs):
#         if not "email" in kwargs:
#             raise ValueError("email must required.")

#         user = self.model(**kwargs)
#         user.set_password(kwargs["password"])
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, email, username, password):
#         user = self.create_user(email=email, username=username, password=password)
#         user.is_superuser = True
#         user.is_active = True
#         user.is_staff = True
#         user.save(using=self._db)
#         return user


class MyAccountManager(BaseUserManager):
    def create_user(self, email, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set.")
        email = self.normalize_email(email)

        if not username:
            username = email.split("@")[0]  # default username from email

        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(
            email, username=username, password=password, **extra_fields
        )


class Account(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(verbose_name="email", max_length=100, unique=True)
    username = models.CharField(max_length=70, unique=True)
    company_name = models.CharField(max_length=50)
    logo = models.ImageField(null=True, blank=True)
    salogan = models.CharField(max_length=100, null=True, blank=True)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    gstin = models.CharField(max_length=15, unique=True)
    pan = models.CharField(max_length=10, unique=True)
    pincode = models.CharField(max_length=6)
    mobile = models.CharField(max_length=10)
    state = models.CharField(max_length=50)
    statecode = models.CharField(max_length=2, choices=GST_STATE_CODE)
    bank_name = models.CharField(max_length=30)
    bank_account = models.CharField(max_length=20)
    bank_ifsc = models.CharField(max_length=11)
    swift_code = models.CharField(max_length=20, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)  # ✅ Add this

    USERNAME_FIELD = "email"

    objects = MyAccountManager()

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return self.username


class Verification(models.Model):
    new_email = models.EmailField(null=True, blank=True)
    email = models.CharField(max_length=64)
    code = models.CharField(max_length=64)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
