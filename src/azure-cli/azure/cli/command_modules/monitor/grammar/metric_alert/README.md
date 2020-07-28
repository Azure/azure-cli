# Working with the ANTLR grammar in Azure CLI

The ANTLR grammar is used to generate expression parsing for the `az monitor metrics alert create/update` commands. Due to the complexity, and introduction of other authoring features, it is *not* recommended that new commands follow this pattern.

## SETUP

To set up your system to be able to alter and regenerate the grammar code, see the QuickStart section on [the ANTLR website](https://www.antlr.org/). You will need to have the Java JDK (JRE is *not* sufficient) installed.

The steps for Windows are replicated here:
```
Download https://www.antlr.org/download/antlr-4.7.2-complete.jar.
Add antlr4-complete.jar to CLASSPATH, either:
Permanently: Using System Properties dialog > Environment variables > Create or append to CLASSPATH variable
Temporarily, at command line:
SET CLASSPATH=.;C:\Javalib\antlr4-complete.jar;%CLASSPATH%
```

You will likely also need to add the path to your JDK bin directory to your PATH.

## MAKING CHANGES

1. Make updates to the `MetricAlertCondition.g4` grammar file.
2. Test your changes by entering a condition expression in a file called `test.txt` and running `run_test.bat`. This will open a GUI where you can visually see how your expression will be parsed--useful in identifying problems with your grammar.
3. Once you are happy with the grammar changes, run `build_python.bat` to update the generated Python classes. Add the license header to the three generated files.
4. Add a test to cover your new scenario.
5. Update the `MetricAlertConditionValidator.py` file until your test passes.
6. Clean up the unneeded Java files `del *.class *.java *.tokens *.interp test.txt`
7. Open a PR. License headers and pylint annotations will be removed during autogeneration, so you will need to reverse those lines.