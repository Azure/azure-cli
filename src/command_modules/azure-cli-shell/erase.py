from azure.cli.core.commands.progress import IndeterminateStandardOut

view = IndeterminateStandardOut()

view.write({'message' : 'test'})

print(view.spinner.label)
