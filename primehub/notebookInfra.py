import os
import ipywidgets

def display_maintenance_tab():
    def lock_repo():
        os.chmod(os.path.join(os.getenv("HOME"), 'index.md'), 0o444)

    def unlock_repo():
        os.chmod(os.path.join(os.getenv("HOME"), 'index.md'), 0o644)

    def protection_mode_change(change):
        if change['new'] != change['old']:
            if change['new'] == 'Protected':
                lock_repo()
            elif change['new'] == 'Dev':
                unlock_repo()
        print('Mode changed!')

    # Protection Mode
    dev_stat = os.access(os.path.join(os.getenv("HOME"), 'index.md'), os.W_OK)
    if dev_stat: # Dev mode
        current_mode = 'Dev'
    else:        # Protected mode
        current_mode = 'Protected'
    protection_mode_buttons = ipywidgets.ToggleButtons(
        options=['Protected', 'Dev'],
        description='Mode:',
        value=current_mode
    )
    protection_mode_buttons.observe(protection_mode_change, 'value')
    protection_tab = ipywidgets.VBox(children=[protection_mode_buttons])

    # Restart Notebook
    def kill_notebook_pod(self):
        print('Maintenance Notebook Pod will be restart ...')
        cmd='kubectl delete pod -n hub -l app.kubernetes.io/name=admin-notebook'
        os.system(cmd)
    
    restart_label_1 = ipywidgets.Label(value='To reset the notebook back to default value, please click the follwoing button.')
    restart_button = ipywidgets.Button(description="Reset Notebook", button_style="danger")
    restart_button.on_click(kill_notebook_pod)
    restart_notebook_tab = ipywidgets.VBox(children=[restart_label_1,restart_button])

    tab = ipywidgets.Tab(children=[restart_notebook_tab, protection_tab])
    tab.set_title(0, 'Restart Notebook')
    tab.set_title(1, 'Notebook Protection')
    return tab
