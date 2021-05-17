from django.shortcuts import render,redirect
from . models import Contact,User,Product,Wishlist,Cart,Transaction
from django.conf import settings	
from django.core.mail import send_mail
import random 
from .paytm import generate_checksum, verify_checksum
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
# Create your views here.


def login_validate_email(request):
	email =request.GET.get('email',None)
	data={
		'is_taken': User.objects.filter(email__iexact=email).exists()
	}
	return JsonResponse(data)

def signup_validate_email(request):
	email =request.GET.get('email',None)
	data={
		'is_taken': User.objects.filter(email__iexact=email).exists()
	}
	return JsonResponse(data)


def initiate_payment(request):
    if request.method == "GET":
        return render(request, 'pay.html')
    cart=""
    try:
    	made_by=User.objects.get(email=request.session['email'])
    	amount = int(request.POST['amount'])
    	carts=Cart.objects.filter(user=made_by,payment_status="pending")
    	for i in carts:
    		cart=cart+str(i.id)+","
    except:
        return render(request, 'pay.html', context={'error': 'Wrong Accound Details or amount'})

    transaction = Transaction.objects.create(made_by=made_by,amount=amount,cart=cart)
    transaction.save()
    merchant_key = settings.PAYTM_SECRET_KEY

    params = (
        ('MID', settings.PAYTM_MERCHANT_ID),
        ('ORDER_ID', str(transaction.order_id)),
        ('CUST_ID', str(transaction.made_by.email)),
        ('TXN_AMOUNT', str(transaction.amount)),
        ('CHANNEL_ID', settings.PAYTM_CHANNEL_ID),
        ('WEBSITE', settings.PAYTM_WEBSITE),
        # ('EMAIL', request.user.email),
        # ('MOBILE_N0', '9911223388'),
        ('INDUSTRY_TYPE_ID', settings.PAYTM_INDUSTRY_TYPE_ID),
        ('CALLBACK_URL', 'http://localhost:8000/callback/'),
        # ('PAYMENT_MODE_ONLY', 'NO'),
    )

    paytm_params = dict(params)
    checksum = generate_checksum(paytm_params, merchant_key)

    transaction.checksum = checksum
    transaction.save()
    
    for i in carts:
    	i.payment_status="completed"
    	i.save()

    paytm_params['CHECKSUMHASH'] = checksum
    print('SENT: ', checksum)
    return render(request, 'redirect.html', context=paytm_params)

@csrf_exempt
def callback(request):
    if request.method == 'POST':
        received_data = dict(request.POST)
        paytm_params = {}
        paytm_checksum = received_data['CHECKSUMHASH'][0]
        for key, value in received_data.items():
            if key == 'CHECKSUMHASH':
                paytm_checksum = value[0]
            else:
                paytm_params[key] = str(value[0])
        # Verify checksum
        is_valid_checksum = verify_checksum(paytm_params, settings.PAYTM_SECRET_KEY, str(paytm_checksum))
        if is_valid_checksum:
            received_data['message'] = "Checksum Matched"
        else:
            received_data['message'] = "Checksum Mismatched"
            return render(request, 'callback.html', context=received_data)
        return render(request, 'callback.html', context=received_data)


def index(request):
	return render(request,'index.html')

def shop(request):
	products=Product.objects.all()
	return render(request,'shop.html',{'products':products})

def checkout(request):
	return render(request,'checkout.html')

def signup(request):
	if request.method=="POST":
		try:
			user=User.objects.get(email=request.POST['email'])
			msg="Email Already Registered"
			return render(request,'signup.html',{'msg':msg})
		except:
			if request.POST['password']==request.POST['cpassword']:
				User.objects.create(

					fname=request.POST['fname'],
					lname=request.POST['lname'],
					mobile=request.POST['mobile'],
					email=request.POST['email'],
					password=request.POST['password'],
					cpassword=request.POST['cpassword'],
					address=request.POST['address'],
					image=request.FILES['image'],
					usertype=request.POST['usertype']
					)
				subject = 'OTP for Registration'
				otp=random.randint(1000,9999)
				message = "Your OTP For Registration Is"+str(otp)
				email_from = settings.EMAIL_HOST_USER 
				recipient_list = [request.POST['email'],] 
				send_mail( subject, message, email_from, recipient_list ) 
			return render(request,'otp.html',{'otp':otp,'email':request.POST['email']})
		else:
			msg="Password and Confirm Password Does Not Matched!"
			return render(request,'signup.html',{'msg':msg})
	else:		
		return render(request,'signup.html')
def login(request):
	if request.method=="POST":
		if request.POST['action']=="Forgot Password":

			return render(request,'enter_email.html')
		else:
			try:
				user=User.objects.get(
					email=request.POST['email'],
					password=request.POST['password']
				)
				if user.usertype=="user":
					request.session['email']=user.email
					request.session['fname']=user.fname
					request.session['image']=user.image.url
					wishlists=Wishlist.objects.filter(user=user)
					request.session['wishlist_count']=len(wishlists)
					carts=Cart.objects.filter(user=user,payment_status="pending")
					request.session['cart_count']=len(carts)
					return render(request,'index.html')
				elif user.usertype=="seller":
					request.session['email']=user.email
					request.session['fname']=user.fname
					request.session['image']=user.image.url
					return render(request,'seller_index.html')

			except Exception as e:
				print(e)
				msg="Email Or Password Is Incorrect"
				return render(request,'login.html',{'msg':msg})
	else:
		return render(request,'login.html')
		
def verify_otp(request):
	otp1=request.POST['otp1']
	otp2=request.POST['otp2']
	email=request.POST['email']
	user=User.objects.get(email=email)
	if otp1==otp2:
		user.status="active"
		user.save()
		msg="User Activated Successfully"
		return render(request,'login.html',{'msg':msg})
	else:
		msg1="Invalid OTP"
		return render(request,'otp.html',{'otp':otp1,'email':email,'msg':msg})

def contact(request):
	if request.method=="POST":
		Contact.objects.create(
				name=request.POST['name'],
				email=request.POST['email'],
				mobile=request.POST['mobile'],
				massage=request.POST['massage']
			)
		msg="Contact saved successfully"
		return render(request,'contact.html',{'msg':msg,})
	else:
		return render(request,'contact.html')

def logout(request):
	try:
		del request.session['email']
		del request.session['fname']
		del request.session['image']
		del request.session['wishlist_count']
		return render(request,'index.html')
	except:
		return render(request,'index.html')

def change_password(request):
	if request.method=="POST":
		user=User.objects.get(email=request.session['email'])

		if user.password==request.POST['old_password']:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.cpassword=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				msg="New Password & Confirm New Password Does Not Matched"
				return render(request,'change_password.html',{'msg':msg})
		else:
			msg="Old Password Is Incorrect"
			return render(request,'change_password.html',{'msg':msg})
	else:
		return render(request,'change_password.html')

def seller_change_password(request):
	if request.method=="POST":
		user=User.objects.get(email=request.session['email'])

		if user.password==request.POST['old_password']:
			if request.POST['new_password']==request.POST['cnew_password']:
				user.password=request.POST['new_password']
				user.cpassword=request.POST['new_password']
				user.save()
				return redirect('logout')
			else:
				msg="New Password & Confirm New Password Does Not Matched"
				return render(request,'seller_change_password.html',{'msg':msg})
		else:
			msg="Old Password Is Incorrect"
			return render(request,'seller_change_password.html',{'msg':msg})
	else:
		return render(request,'seller_change_password.html')

def enter_email(request):
	try:
		user=User.objects.get(email=request.POST['email'])
		subject = 'OTP for Forgot password'
		otp=random.randint(1000,9999)
		message = "Your OTP For Forgot Password Is" +str(otp)
		email_from = settings.EMAIL_HOST_USER 
		recipient_list = [request.POST['email'],] 
		send_mail( subject, message, email_from, recipient_list ) 
		return render(request,'forgot_otp.html',{'otp':otp,'email':request.POST['email']})
	except:
		msg="Email Not Found"
		return render(request,'enter_email.html',{'msg':msg})

def forgot_verify_otp(request):
	otp1=request.POST['otp1']
	otp2=request.POST['otp2']
	email=request.POST['email']
	user=User.objects.get(email=email)
	if otp1==otp2:
		return render(request,'new_password.html',{'email':email})
	else:
		msg="Invalid otp"
		return render(request,'forgot_otp.html',{'otp':otp,'email':email})

def new_password(request):
	email=request.POST['email']
	user=User.objects.get(email=email)
	if request.POST['new_password']==request.POST['cnew_password']:
		user.password=request.POST['new_password']
		user.cpassword=request.POST['new_password']
		user.save()
		msg="Password Updated Successfully"
		return render(request,'login.html',{'msg':msg})
	else:
		msg1="New Password & New Confirm Password Does Not Matched"
		return render(request,'new_password.html',{'email':email,'msg1':msg1})





def seller_enter_email(request):
	try:
		user=User.objects.get(email=request.POST['email'])
		subject = 'OTP for Forgot password'
		otp=random.randint(1000,9999)
		message = "Your OTP For Forgot Password Is" +str(otp)
		email_from = settings.EMAIL_HOST_USER 
		recipient_list = [request.POST['email'],] 
		send_mail( subject, message, email_from, recipient_list ) 
		return render(request,'seller_forgot_otp.html',{'otp':otp,'email':request.POST['email']})
	except:
		msg="Email Not Found"
		return render(request,'seller_enter_email.html',{'msg':msg})

def seller_forgot_verify_otp(request):
	otp1=request.POST['otp1']
	otp2=request.POST['otp2']
	email=request.POST['email']
	user=User.objects.get(email=email)
	if otp1==otp2:
		return render(request,'seller_new_password.html',{'email':email})
	else:
		msg="Invalid otp"
		return render(request,'seller_forgot_otp.html',{'otp':otp,'email':email})

def seller_new_password(request):
	email=request.POST['email']
	user=User.objects.get(email=email)
	if request.POST['new_password']==request.POST['cnew_password']:
		user.password=request.POST['new_password']
		user.cpassword=request.POST['new_password']
		user.save()
		msg="Password Updated Successfully"
		return render(request,'login.html',{'msg':msg})
	else:
		msg1="New Password & New Confirm Password Does Not Matched"
		return render(request,'new_password.html',{'email':email,'msg1':msg1})

def edit_profile(request):
	user=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		user.fname=request.POST['fname']
		user.lname=request.POST['lname']
		user.email=request.POST['email']
		user.mobile=request.POST['mobile']
		user.address=request.POST['address']
		user.gender=request.POST['gender']
		try:
			user.image=request.FILES['image']
			user.save()
			request.session['image']=user.image.url
			return redirect('index')
		except:
			user.save()
			return redirect('index')


	else:
		return render(request,'edit_profile.html',{'user':user})

def seller_add_product(request):
	seller=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		Product.objects.create(
			seller=seller,
			product_category=request.POST['product_category'],
			product_brand=request.POST['product_brand'],
			product_price=request.POST['product_price'],
			product_color=request.POST['product_color'],
			product_size=request.POST['product_size'],
			product_description=request.POST['product_description'],
			product_image=request.FILES['product_image'])
		msg="Product Added Successfully"
		return render(request,'seller_add_product.html',{'msg':msg})
	else:
		return render(request,'seller_add_product.html')


def seller_index(request):
	return render(request,'seller_index.html')

def seller_view_product(request):
	seller=User.objects.get(email=request.session['email'])
	products=Product.objects.filter(seller=seller)
	return render(request,'seller_view_product.html',{'product':products})

def seller_edit_product(request,pk):
	product=Product.objects.get(pk=pk)
	if request.method=="POST":
		product.product_brand=request.POST['product_brand']
		product.product_price=request.POST['product_price']
		product.product_color=request.POST['product_color']
		product.product_size=request.POST['product_size']
		product.product_description=request.POST['product_description']
		try:
			product.product_image=request.FILES['product_image']
			product.save()
		except:
			pass
		product.save()
		return redirect('seller_view_product')

	else:
		return render(request,'seller_edit_product.html',{'product':product})

def seller_product_detail(request,pk):
	product=Product.objects.get(pk=pk)
	return render(request,'seller_product_detail.html',{'product':product})

def seller_delete_product(request,pk):
	product=Product.objects.get(pk=pk)
	product.delete()
	return redirect('seller_view_product')

def user_product_detail(request,pk):
	flag=False
	flag1=False
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	try:
		Wishlist.objects.get(user=user,product=product)
		flag=True
	except:
		pass
	try:
		Cart.objects.get(user=user,product=product,payment_status="pending")
		flag1=True
	except:
		pass
	return render(request,'user_product_detail.html',{'product':product,'flag':flag ,'flag1':flag1})

def wishlist(request):
	user=User.objects.get(email=request.session['email'])
	wishlists=Wishlist.objects.filter(user=user)
	request.session['wishlist_count']=len(wishlists)
	return render(request,'wishlist.html',{'wishlists':wishlists})

def add_to_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	Wishlist.objects.create(user=user,product=product)
	return redirect('wishlist')

def remove_from_wishlist(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	wishlist=Wishlist.objects.get(user=user,product=product)
	wishlist.delete()
	return redirect('wishlist')

def mycart(request):
	net_price=0
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.filter(user=user,payment_status="pending")
	for i in cart:
		net_price=net_price+i.total_price

	request.session['cart_count']=len(cart)
	return render(request,'mycart.html',{'cart':cart,'net_price':net_price})

def add_to_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	price=product.product_price
	total_price=product.product_price
	Cart.objects.create(
			user=user,
			product=product,
			price=price,
			total_price=total_price
		)
	return redirect('mycart')

def remove_from_cart(request,pk):
	product=Product.objects.get(pk=pk)
	user=User.objects.get(email=request.session['email'])
	cart=Cart.objects.get(product=product,user=user)
	cart.delete()
	return redirect('mycart')

def change_qty(request):
	cart=Cart.objects.get(pk=request.POST['pk'])
	cart.qty=int(request.POST['qty'])
	cart.total_price=cart.price*int(request.POST['qty'])
	cart.save()
	return redirect('mycart')

def myorder(request):
	user=User.objects.get(email=request.session['email'])
	transactions=Transaction.objects.filter(made_by=user)
	return render(request,'myorder.html',{'transactions':transactions})

def user_order_details(request,pk):
	transactions=Transaction.objects.get(pk=pk)
	carts=transactions.cart.split(",")[:-1]
	order_carts=[]
	for i in carts:
		order_carts.append(Cart.objects.get(pk=int(i)))
	return render(request,'user_order_details.html',{'transactions':transactions,'order_carts':order_carts})

def user_edit_profile(request):
	user=User.objects.get(email=request.session['email'])
	if request.method=="POST":
		user.fname=request.POST['fname']
		user.lname=request.POST['lname']
		user.mobile=request.POST['mobile']
		user.email=request.POST['email']
		user.address=request.POST['address']
		try:
			user.image=request.FILES['image']
		except:
			pass
		user.save()
		msg="Profile Updated Successfully"
		user=User.objects.get(email=request.session['email'])
		request.session['image']=user.image.url
		return render(request,'user_edit_profile.html',{'user':user,'msg':msg})
	else:
		return render(request,'user_edit_profile.html',{'user':user})

def user_product_search(request):
	if request.method=="POST":
		product_category=request.POST['product_category']
		products=Product.objects.filter(product_category=product_category)
		return render(request,'user_product_search.html',{'products':products})
	else:
		return render(request,'user_product_search.html')









