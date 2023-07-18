echo off
echo Testing AutoscaleCondition
call antlr AutoscaleCondition.g4
call javac Autoscale*.java
call grun AutoscaleCondition expression test.txt -gui
