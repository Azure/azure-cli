Azure CLI Interactive Shell
***************************

The interactive shell for Microsoft Azure CLI (Command Line Interface)
######################################################################

* Interactive Tutorials
* Lightweight Drop Down Completions 
* Auto Cached Suggestions 
* Dynamic parameter completion 
* Defaulting scopes of commands
* On the fly descriptions of the commands AND parameters 
* On the fly examples of how to utilize each command 
* Optional "az" component 
* Query the previous command
* Navigation of example pane 
* Optional layout configurations 
* Fun Colors 


Running
#######

To start the application

.. code-block:: console

   $ az shell


Then type your commands and hit [Enter]

To use commands outside the application

.. code-block:: console

   $ #[command]


To Search through the last command as json
jmespath format for querying

.. code-block:: console

   $ ? [param]


*Note: Only if the previous command dumps out json, e.g. vm list*

To only see the commands for a command

.. code-block:: console

   $ %% [top-level command] [sub-level command] etc
 

To undefault a value

.. code-block:: console

   $ %% ..


Use Examples
############

Type a command, for example:

.. code-block:: console

   $ vm create


Look at the examples

*Scroll through the pane with Control Y for up and Control N for down #*

Pick the example you want with:

.. code-block:: console

   $ vm create :: [Example Number]


Dev Setup
#########

Fork and clone repository

.. code-block:: console

   $ . dev_setup.py


To get the Exit Code of the previous command:

.. code-block:: console

   $ $


Clear History
#############

Only clears the appended suggestion when you restart the shell

.. code-block:: console

   $ clear-history

