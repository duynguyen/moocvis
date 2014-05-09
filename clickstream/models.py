# from google.appengine.ext import ndb

# Create your models here.
def user_list(request):
    users = User.objects.order_by('name')
    return render(request, 'book_list.html', {'books': books})