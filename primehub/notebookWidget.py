import ipywidgets
import time

def multi_checkbox_widget(descriptions):
    """ Widget with a search field and lots of checkboxes """
    search_widget = ipywidgets.Text()
    options_dict = {description: ipywidgets.Checkbox(description=description, value=False, layout=ipywidgets.Layout(height='20px')) for description in descriptions}
    options = [options_dict[description] for description in descriptions]
    options_widget = ipywidgets.VBox(options, layout={'overflow': 'scroll'})
    multi_select = ipywidgets.VBox([search_widget, options_widget])

    # Wire the search field to the checkboxes
    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = [options_dict[description] for description in descriptions]
        else:
            matches = [x for x in descriptions if x.startswith(search_input)]
            new_options = [options_dict[description] for description in matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names='value')
    return multi_select
