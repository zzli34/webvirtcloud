from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from accounts.models import UserInstance, UserSSHKey
from instances.models import Instance
from accounts.forms import UserAddForm


def profile(request):
    """
    :param request:
    :return:
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))

    error_messages = []
    user = User.objects.get(id=request.user.id)
    publickeys = UserSSHKey.objects.filter(user_id=request.user.id)

    if request.method == 'POST':
        if 'username' in request.POST:
            username = request.POST.get('username', '')
            email = request.POST.get('email', '')
            user.first_name = username
            user.email = email
            user.save()
            return HttpResponseRedirect(request.get_full_path())
        if 'oldpasswd' in request.POST:
            oldpasswd = request.POST.get('oldpasswd', '')
            password1 = request.POST.get('passwd1', '')
            password2 = request.POST.get('passwd2', '')
            if not password1 or not password2:
                error_messages.append("Passwords didn't enter")
            if password1 and password2 and password1 != password2:
                error_messages.append("Passwords don't match")
            if not user.check_password(oldpasswd):
                error_messages.append("Old password is wrong!")
            if not error_messages:
                user.set_password(password1)
                user.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'keyname' in request.POST:
            keyname = request.POST.get('keyname', '')
            keypublic = request.POST.get('keypublic', '')
            for key in publickeys:
                if keyname == key.keyname:
                    msg = _("Key name already exist")
                    error_messages.append(msg)
                if keypublic == key.keypublic:
                    msg = _("Public key already exist")
                    error_messages.append(msg)
            if not error_messages:
                addkeypublic = UserSSHKey(user_id=request.user.id, keyname=keyname, keypublic=keypublic)
                addkeypublic.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'keydelete' in request.POST:
            keyid = request.POST.get('keyid', '')
            delkeypublic = UserSSHKey.objects.get(id=keyid)
            delkeypublic.delete()
            return HttpResponseRedirect(request.get_full_path())
    return render(request, 'profile.html', locals())


def accounts(request):
    """
    :param request:
    :return:
    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))

    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    error_messages = []
    users = User.objects.filter(is_staff=False, is_superuser=False)

    if request.method == 'POST':
        if 'create' in request.POST:
            form = UserAddForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
            else:
                for msg_err in form.errors.values():
                    error_messages.append(msg_err.as_text())
            if not error_messages:
                new_user = User.objects.create_user(data['name'], None, data['password'])
                new_user.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'edit' in request.POST:
            user_id = request.POST.get('user_id', '')
            user_pass = request.POST.get('user_pass', '')
            user_edit = User.objects.get(id=user_id)
            user_edit.set_password(user_pass)
            user_edit.save()
            return HttpResponseRedirect(request.get_full_path())
        if 'block' in request.POST:
            user_id = request.POST.get('user_id', '')
            user_block = User.objects.get(id=user_id)
            user_block.is_active = False
            user_block.save()
            return HttpResponseRedirect(request.get_full_path())
        if 'unblock' in request.POST:
            user_id = request.POST.get('user_id', '')
            user_unblock = User.objects.get(id=user_id)
            user_unblock.is_active = True
            user_unblock.save()
            return HttpResponseRedirect(request.get_full_path())
        if 'delete' in request.POST:
            user_id = request.POST.get('user_id', '')
            try:
                del_user_inst = UserInstance.objects.filter(user_id=user_id)
                del_user_inst.delete()
            finally:
                user_delete = User.objects.get(id=user_id)
                user_delete.delete()
            return HttpResponseRedirect(request.get_full_path())

    return render(request, 'accounts.html', locals())


def account(request, user_id):
    """
    :param request:
    :return:
    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('index'))

    if not request.user.is_superuser:
        return HttpResponseRedirect(reverse('index'))

    error_messages = []
    user = User.objects.get(id=user_id)
    user_insts = UserInstance.objects.filter(user_id=user_id)
    instances = Instance.objects.all()

    if user.username == request.user.username:
        return HttpResponseRedirect(reverse('profile'))

    if request.method == 'POST':
        if 'delete' in request.POST:
            user_inst = request.POST.get('user_inst', '')
            del_user_inst = UserInstance.objects.get(id=user_inst)
            del_user_inst.delete()
            return HttpResponseRedirect(request.get_full_path())
        if 'permission' in request.POST:
            user_inst = request.POST.get('user_inst', '')
            inst_vnc = request.POST.get('inst_vnc', '')
            inst_change = request.POST.get('inst_change', '')
            inst_delete = request.POST.get('inst_delete', '')
            edit_user_inst = UserInstance.objects.get(id=user_inst)
            edit_user_inst.is_change = bool(inst_change)
            edit_user_inst.is_delete = bool(inst_delete)
            edit_user_inst.is_vnc = bool(inst_vnc)
            edit_user_inst.save()
            return HttpResponseRedirect(request.get_full_path())
        if 'add' in request.POST:
            inst_id = request.POST.get('inst_id', '')
            try:
                check_inst = UserInstance.objects.get(instance_id=int(inst_id))
                msg = _("Instance already added")
                error_messages.append(msg)
            except UserInstance.DoesNotExist:
                add_user_inst = UserInstance(instance_id=int(inst_id), user_id=user_id)
                add_user_inst.save()
                return HttpResponseRedirect(request.get_full_path())

    return render(request, 'account.html', locals())
