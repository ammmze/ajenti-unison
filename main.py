import backend
import logging
from ajenti.api import *
from ajenti.ui import *
from ajenti.standalone import make_log

class UnisonPlugin(CategoryPlugin):
    text = 'Unison'
    icon = '/dl/hosts/icon.png'
    folder = 'system'

    log = make_log(debug=True)
 
    def on_init(self):
    	self.hosts = []
        self.config = backend.Config(self.app)
    	self.profiles = self.config.read_profiles()
 
    def on_session_start(self):
        # _vars are session-persisted
        self._quickediting = None # this will indicate if we are in editing dialog
        self._editing = None # this will indicate if we are in editing full profile
        self._editing_param = None # this will indicate if we are in editing a profile param
 
    def get_ui(self):
        if (self._editing is not None):
            ui = self.get_edit_ui()
        else:
            ui = self.get_main_ui()
 
        return ui

    def get_main_ui(self):
        ui = self.app.inflate('unison:main')
        t = ui.find('profiles')
 
        for p in self.profiles:
            if (p.is_running()):
                start_stop = UI.TipIcon(
                    icon='/dl/core/ui/stock/service-stop.png',
                    id='stop/' + str(self.profiles.index(p)),
                    text='Stop Unison Profile'
                )
            else:
                start_stop = UI.TipIcon(
                    icon='/dl/core/ui/stock/service-run.png',
                    id='start/' + str(self.profiles.index(p)),
                    text='Start Unison Profile'
                )
            
            t.append(UI.DTR(
                UI.Label(text=p.name),
                UI.Label(text=p.get_root1()),
                UI.Label(text=p.get_root2()),
                UI.Label(text=p.get_status()),
                UI.HContainer(
                    start_stop,
                    UI.TipIcon(
                        icon='/dl/core/ui/stock/edit.png',
                        id='edit/' + str(self.profiles.index(p)),
                        text='Edit'
                    ),
                    UI.TipIcon(
                        icon='/dl/core/ui/stock/edit.png',
                        id='quickedit/' + str(self.profiles.index(p)),
                        text='Quick Edit'
                    ),
                    UI.TipIcon(
                        icon='/dl/core/ui/stock/delete.png',
                        id='del/' + str(self.profiles.index(p)),
                        text='Delete',
                        warning='Remove %s from hosts'%p.name
                    )
                ),
            ))

        if self._quickediting is not None:
            try:
                p = self.profiles[self._quickediting]
            except:
                p = backend.Host()
            d = self.app.inflate('unison:quickedit') # inflate and fill the dialog
            d.find('name').set('value', p.name)
            d.find('root1').set('value', p.get_root1())
            d.find('root2').set('value', p.get_root2())
            ui.append('main', d) # and append it to main UI

        return ui

    def get_edit_ui(self):
        ui = self.app.inflate('unison:edit')
        t = ui.find('profile_attributes')
 
        profile = self.profiles[self._editing]
        profile_index = self.profiles.index(profile)
        params = self.profiles[self._editing].params
        for p in params:
            param_index = profile.params.index(p)
            t.append(UI.DTR(
                UI.Label(text=p['key']),
                UI.Label(text=p['value']),
                UI.HContainer(
                    UI.TipIcon(
                        icon='/dl/core/ui/stock/edit.png',
                        id='editParam/' + str(profile_index) + '/' + str(param_index),
                        text='Edit'
                    ),
                    UI.TipIcon(
                        icon='/dl/core/ui/stock/delete.png',
                        id='delParam/' + str(profile_index) + '/' + str(param_index),
                        text='Delete',
                        warning='Remove parameter %s from profile %s' % (p['key'], profile.name)
                    )
                ),
            ))

        if self._editing_param is not None:
            try:
                p = self.profiles[self._editing]
            except:
                p = backend.Profile(self.config)

            #try:
            if type(self._editing_param) == int:
                param = p.params[self._editing_param]
            else:
                param = p.blank_param()
            
            d = self.app.inflate('unison:paramedit') # inflate and fill the dialog
            d.find('key').set('value', param['key'])
            d.find('value').set('value', param['value'])
            ui.append('main', d) # and append it to main UI
            #except:
            #    print 'Could not find param to edit'

        return ui
 
    @event('button/click')
    def on_click(self, event, params, vars = None):
        if params[0] == 'add':
            self._editing = len(self.hosts) # new profile
        if params[0] == 'edit':
            self._editing = int(params[1]) # edit selected profile
        if params[0] == 'start':
            self.profiles[int(params[1])].start() # start selected profile
        if params[0] == 'stop':
            self.profiles[int(params[1])].stop() # stop selected profile
        if params[0] == 'quickedit':
            self._quickediting = int(params[1]) # quick edit selected profile
        if params[0] == 'del':
            self.profiles.pop(int(params[1]))
            #backend.Config(self.app).save(self.hosts)
        if params[0] == 'addParam':
            self._editing_param = 'add' # selected host
        if params[0] == 'editParam':
            self._editing = int(params[1]) # selected host
            self._editing_param = int(params[2]) # selected host
        if params[0] == 'delParam':
            self.profiles[int(params[1])].params.pop(int(params[2]))
            self.profiles[int(params[1])].save()
            #backend.Config(self.app).save(self.hosts)
        if params[0] == 'cancelProfileEdit':
            self._editing = None # new profile
 
 
    @event('dialog/submit')
    def on_submit(self, event, params, vars = None):
        if params[0] == 'dlgEdit':
            if vars.getvalue('action', '') == 'OK':
                try:
                    p = self.profiles[self._quickediting]
                except:
                    p = backend.Profile(self.config)

                p.name = vars.getvalue('name', '')
                p.set_root1(vars.getvalue('root1',''))
                p.set_root2(vars.getvalue('root2',''))

                try:
                    self.profiles[self._quickediting] = p
                except:
                    self.profiles.append(p)

                p.save()
                #backend.Config(self.app).save(self.hosts)
            self._quickediting = None
        if params[0] == 'dlgParamEdit':
            if vars.getvalue('action', '') == 'OK':
                try:
                    p = self.profiles[self._editing]
                    key = vars.getvalue('key', None)
                    value = vars.getvalue('value', '')
                    if key is not None:

                        if type(self._editing_param) == int:
                            index = self._editing_param
                        else:
                            index = None

                        try:
                            p.set_param(key, value, index)
                        except:
                            print 'Could not setParam'
                        p.save()
                        self.profiles[self._editing] = p
                    else:
                        print 'No key specified, delete the parameter'
                except:
                    print 'Could not save profile parameter'
                
            self._editing_param = None