from django.db import models

# Create your models here.
from django.db import models

from users.models import Account

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
    ("38", "NA"),
)

CURRENCY_CODE = (
    ("USD", "US Dollar"),
    ("CAD", "Canadian Dollar"),
    ("EUR", "Euro"),
    ("AED", "United Arab Emirates Dirham"),
    ("AFN", "Afghan Afghani"),
    ("ALL", "Albanian Lek"),
    ("AMD", "Armenian Dram"),
    ("ARS", "Argentine Peso"),
    ("AUD", "Australian Dollar"),
    ("AZN", "Azerbaijani Manat"),
    ("BAM", "Bosnia-Herzegovina Convertible Mark"),
    ("BDT", "Bangladeshi Taka"),
    ("BGN", "Bulgarian Lev"),
    ("BHD", "Bahraini Dinar"),
    ("BIF", "Burundian Franc"),
    ("BND", "Brunei Dollar"),
    ("BOB", "Bolivian Boliviano"),
    ("BRL", "Brazilian Real"),
    ("BWP", "Botswanan Pula"),
    ("BYN", "Belarusian Ruble"),
    ("BZD", "Belize Dollar"),
    ("CDF", "Congolese Franc"),
    ("CHF", "Swiss Franc"),
    ("CLP", "Chilean Peso"),
    ("CNY", "Chinese Yuan"),
    ("COP", "Colombian Peso"),
    ("CRC", "Costa Rican Colón"),
    ("CVE", "Cape Verdean Escudo"),
    ("CZK", "Czech Republic Koruna"),
    ("DJF", "Djiboutian Franc"),
    ("DKK", "Danish Krone"),
    ("DOP", "Dominican Peso"),
    ("DZD", "Algerian Dinar"),
    ("EEK", "Estonian Kroon"),
    ("EGP", "Egyptian Pound"),
    ("ERN", "Eritrean Nakfa"),
    ("ETB", "Ethiopian Birr"),
    ("GBP", "British Pound Sterling"),
    ("GEL", "Georgian Lari"),
    ("GHS", "Ghanaian Cedi"),
    ("GNF", "Guinean Franc"),
    ("GTQ", "Guatemalan Quetzal"),
    ("HKD", "Hong Kong Dollar"),
    ("HNL", "Honduran Lempira"),
    ("HRK", "Croatian Kuna"),
    ("HUF", "Hungarian Forint"),
    ("IDR", "Indonesian Rupiah"),
    ("ILS", "Israeli New Sheqel"),
    ("INR", "Indian Rupee"),
    ("IQD", "Iraqi Dinar"),
    ("IRR", "Iranian Rial"),
    ("ISK", "Icelandic Króna"),
    ("JMD", "Jamaican Dollar"),
    ("JOD", "Jordanian Dinar"),
    ("JPY", "Japanese Yen"),
    ("KES", "Kenyan Shilling"),
    ("KHR", "Cambodian Riel"),
    ("KMF", "Comorian Franc"),
    ("KRW", "South Korean Won"),
    ("KWD", "Kuwaiti Dinar"),
    ("KZT", "Kazakhstani Tenge"),
    ("LBP", "Lebanese Pound"),
    ("LKR", "Sri Lankan Rupee"),
    ("LTL", "Lithuanian Litas"),
    ("LVL", "Latvian Lats"),
    ("LYD", "Libyan Dinar"),
    ("MAD", "Moroccan Dirham"),
    ("MDL", "Moldovan Leu"),
    ("MGA", "Malagasy Ariary"),
    ("MKD", "Macedonian Denar"),
    ("MMK", "Myanma Kyat"),
    ("MOP", "Macanese Pataca"),
    ("MUR", "Mauritian Rupee"),
    ("MXN", "Mexican Peso"),
    ("MYR", "Malaysian Ringgit"),
    ("MZN", "Mozambican Metical"),
    ("NAD", "Namibian Dollar"),
    ("NGN", "Nigerian Naira"),
    ("NIO", "Nicaraguan Córdoba"),
    ("NOK", "Norwegian Krone"),
    ("NPR", "Nepalese Rupee"),
    ("NZD", "New Zealand Dollar"),
    ("OMR", "Omani Rial"),
    ("PAB", "Panamanian Balboa"),
    ("PEN", "Peruvian Nuevo Sol"),
    ("PHP", "Philippine Peso"),
    ("PKR", "Pakistani Rupee"),
    ("PLN", "Polish Zloty"),
    ("PYG", "Paraguayan Guarani"),
    ("QAR", "Qatari Rial"),
    ("RON", "Romanian Leu"),
    ("RSD", "Serbian Dinar"),
    ("RUB", "Russian Ruble"),
    ("RWF", "Rwandan Franc"),
    ("SAR", "Saudi Riyal"),
    ("SDG", "Sudanese Pound"),
    ("SEK", "Swedish Krona"),
    ("SGD", "Singapore Dollar"),
    ("SOS", "Somali Shilling"),
    ("SYP", "Syrian Pound"),
    ("THB", "Thai Baht"),
    ("TND", "Tunisian Dinar"),
    ("TOP", "Tongan Paʻanga"),
    ("TRY", "Turkish Lira"),
    ("TTD", "Trinidad and Tobago Dollar"),
    ("TWD", "New Taiwan Dollar"),
    ("TZS", "Tanzanian Shilling"),
    ("UAH", "Ukrainian Hryvnia"),
    ("UGX", "Ugandan Shilling"),
    ("UYU", "Uruguayan Peso"),
    ("UZS", "Uzbekistan Som"),
    ("VEF", "Venezuelan Bolívar"),
    ("VND", "Vietnamese Dong"),
    ("XAF", "CFA Franc BEAC"),
    ("XOF", "CFA Franc BCEAO"),
    ("YER", "Yemeni Rial"),
    ("ZAR", "South African Rand"),
    ("ZMK", "Zambian Kwacha"),
    ("ZWL", "Zimbabwean Dollar"),
)


class Client(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=50, blank=True, null=True)
    gstin = models.CharField(max_length=50, blank=True, null=True)
    aadhar = models.CharField(max_length=12, blank=True, null=True)
    panno = models.CharField(max_length=20, blank=True, null=True)
    pincode = models.CharField(max_length=6, blank=True, null=True)
    mobile = models.CharField(max_length=12, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    state = models.CharField(max_length=50, default="HARYANA")
    statecode = models.CharField(max_length=2, choices=GST_STATE_CODE, default="6")
    currency = models.CharField(max_length=3, choices=CURRENCY_CODE, default="INR")
    country = models.CharField(max_length=150, default="India")

    def __str__(self):
        return f"{self.id}-{self.name}-{self.address}-{self.city}"

    class Meta:
        db_table = "client"
        ordering = ("-id",)

    def save(self, *args, **kwargs):
        get_state = [
            gst[1] if self.statecode == gst[0] else None for gst in GST_STATE_CODE
        ][0]
        # self.state = get_state

        super().save(*args, **kwargs)
