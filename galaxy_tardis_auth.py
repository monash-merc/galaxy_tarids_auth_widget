#!/usr/bin/python
myTardisServer="https://mytardis.ammrf.org.au/"
galaxyServer="https://galaxy.ammrf.org.au/"
import json
import requests
import base64
import StringIO
import os
import wx
from HTMLParser import HTMLParser

class genericForm(HTMLParser):
    def __init__(self,*args,**kwargs):
        HTMLParser.__init__(self)
        self.processingForm=False
        self.processingOption=False
        self.attrs={}
        self.options=[]
        self.inputs={}

    def handle_starttag(self,tag,attrs):
        if tag == 'form':
            d={}
            for attr in attrs:
                self.attrs[attr[0]]=attr[1]
            self.processingForm=True
        if self.processingForm and tag == 'input':
            dattrs={}
            for attr in attrs:
                dattrs[attr[0]]=attr[1]
            if dattrs.has_key('name'):
                if dattrs.has_key('value'):
                    self.inputs[dattrs['name']]=dattrs['value']
                else:
                    self.inputs[dattrs['name']]=None

    def handle_endtag(self,tag):
        if tag == 'form':
            self.processingForm=False

class genericLogin(wx.Dialog):
    def __init__(self,msg=None,username=None,*args,**kwargs):
        super(genericLogin,self).__init__(*args,**kwargs)
        self.msg=msg
        
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        if self.msg!=None:
            t=wx.StaticText(self,wx.ID_ANY,label=msg)
            self.GetSizer().Add(t,flag=wx.CENTER|wx.ALL,border=10)

        p=wx.Panel(self)
        p.SetSizer(wx.FlexGridSizer(2,2))
        self.GetSizer().Add(p)
        p.SetSizer(wx.FlexGridSizer(2,2))
        t=wx.StaticText(p,wx.ID_ANY,label='Username')
        p.GetSizer().Add(t,flag=wx.ALL,border=5)
        t = wx.TextCtrl(p,wx.ID_ANY,size=(100,-1),name='username')
        if username!=None:
            t.SetValue(username)
        p.GetSizer().Add(t,flag=wx.EXPAND|wx.ALL,border=5)
        t=wx.StaticText(p,wx.ID_ANY,label='Password')
        p.GetSizer().Add(t,flag=wx.ALL,border=5)
        t = wx.TextCtrl(p,wx.ID_ANY,size=(400,-1),style=wx.TE_PASSWORD,name='password')
        p.GetSizer().Add(t,flag=wx.EXPAND|wx.ALL,border=5)
        

        p=wx.Panel(self)
        p.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        self.GetSizer().Add(p)
        b=wx.Button(p,wx.ID_OK,label="OK")
        b.Bind(wx.EVT_BUTTON,self.onClose)
        p.GetSizer().Add(b)
        b=wx.Button(p,wx.ID_CANCEL,label="Cancel")
        b.Bind(wx.EVT_BUTTON,self.onClose)
        p.GetSizer().Add(b)
        self.Fit()
        

    def onClose(self,event):
        self.EndModal(event.GetEventObject().GetId())

    def getUser(self):
        return self.FindWindowByName('username').GetValue()

    def getPassword(self):
        return self.FindWindowByName('password').GetValue()

class GalaxyLogin(genericLogin):
    def __init__(self,fail=False,*args,**kwargs):
        if fail:
            super(GalaxyLogin,self).__init__(msg="Sorry. Your username or password was incorrect. Please enter details to login to galaxy:",*args,**kwargs)
        else:
            super(GalaxyLogin,self).__init__(msg="Please enter details to login to galaxy:",*args,**kwargs)
class TardisLogin(genericLogin):
    def __init__(self,fail=False,*args,**kwargs):
        if fail:
            super(TardisLogin,self).__init__(msg="Sorry. Your username or password was incorrect. Please enter details to login to tardis:",*args,**kwargs)
        else:
            super(TardisLogin,self).__init__(msg="Please enter details to login to MyTardis:",*args,**kwargs)

    




class MainFrame(wx.Frame):

    def __init__(self):
        super(MainFrame,self).__init__(parent=None)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        msg=""" 
This is an application for EMAP users to setup authentication between Galax and MyTardis
It will produce a file containing the MyTardis API key (stored in ~/.mytardis/mytardis.key
This file needs to be kept secret (it is equilivent to your MyTardis password)"""

        t=wx.StaticText(self,wx.ID_ANY,msg)
        
        self.GetSizer().Add(t,flag=wx.CENTER|wx.ALL,border=10)
        p=wx.Panel(self)
        p.SetSizer(wx.BoxSizer(wx.HORIZONTAL))
        b=wx.Button(p,wx.ID_ANY,"Configure Authentication")
        b.Bind(wx.EVT_BUTTON,self.doIt)
        p.GetSizer().Add(b,flag=wx.CENTER)
        b=wx.Button(p,wx.ID_ANY,"Exit")
        b.Bind(wx.EVT_BUTTON,self.onClose)
        p.GetSizer().Add(b,flag=wx.CENTER)
        self.GetSizer().Add(p,flag=wx.CENTER|wx.ALL|wx.EXPAND,proportion=1,border=10)
        self.Fit()

    def onClose(self,event):
        self.Destroy()

    def doIt(self,event):
        apikey=self.getTardisAPIKey()
        if (apikey != False):
            self.setAPIKeyInGalaxy(apikey)
            self.setAPIKeyInFilesystem(apikey)

    def getTardisAPIKey(self):
        authenticated=False
        retry=False
        while not authenticated:
            if retry:
                user=dlg.getUser()
                dlg=TardisLogin(parent=self,fail=True,username=user)
            else:
                dlg=TardisLogin(parent=self)
            retval=dlg.ShowModal()
            if retval==wx.ID_OK:
                wx.BeginBusyCursor()
                s=requests.Session()
                authData={'username':dlg.getUser(),'password':dlg.getPassword()}
                url="%s/login/"%myTardisServer
                r=s.post(url,data=authData)
                wx.EndBusyCursor()
                if not 'Login' in r.text:
                    authenticated=True
                retry=True
            else:
                break

        if authenticated:
            url="%s/download/api_key/"%myTardisServer
            wx.BeginBusyCursor()
            r=s.get(url)
            wx.EndBusyCursor()
            return r.text
        else:
            return False

    def setAPIKeyInGalaxy(self,apikey):
        apiFile=StringIO.StringIO(apikey)
        authenticated=False
        url="%s/user/login/"%galaxyServer
        retry=False
        while not authenticated:
            if retry:
                user=dlg.getUser()
                dlg=GalaxyLogin(parent=self,fail=True,username=user)
            else:
                dlg=GalaxyLogin(parent=self)
            retval=dlg.ShowModal()
            if retval == wx.ID_OK:
                authData={'email':dlg.getUser(),'password':dlg.getPassword()}
                wx.BeginBusyCursor()
                s=requests.Session()
                r=s.get(url)
                p=genericForm()
                p.feed(r.text)
                p.inputs.update(authData)
                r=s.post(url,data=p.inputs)
                wx.EndBusyCursor()
                if "You are now logged in" in r.text:
                    authenticated=True
                retry=True
            else:
                break
        if authenticated:
            url="%s/user/mytardis_api_keys?cntrller=user"%galaxyServer
            wx.BeginBusyCursor()
            r=s.get(url)
            p=genericForm()
            p.feed(r.text)
            # not sure if its necessary to post both data and files, but since galaxy doesn't allow the API key to be reset, and Tardis doesn't allow generating a new key, its kind of difficult to test
            del p.inputs['new_mytardis_api_key_file']
            r=s.post(url,data=p.inputs,files={'new_mytardis_api_key_file':("chrishines.key",apiFile)})
            wx.EndBusyCursor()
            return True
        else:
            return False

    def setAPIKeyInFilesystem(self,apikey):
        try:
            path=os.path.join(os.path.expanduser('~'), '.mytardis')
            os.mkdir(path,0700)
        except OSError:
            pass
        filename=os.path.join(path,'mytardis.key')
        with open(filename,'w') as f:
            os.chmod(filename,0600)
            f.write(apikey)

app=wx.PySimpleApp()
frame=MainFrame().Show()

app.MainLoop()
