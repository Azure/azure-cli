echo off
echo Testing MetricAlertCondition
call antlr MetricAlertCondition.g4
call javac Metric*.java
call grun MetricAlertCondition expression test.txt -gui
