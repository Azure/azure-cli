FOR /L %%x IN (1,1,2) DO (
    az account set -s "a1bfa635-f2bf-42f1-86b5-848c674fc321"
    azdev test --live --lf --no-exitfirst
    azdev test --live --lf --no-exitfirst --series
    az account set s "28cbf98f-381d-4425-9ac4-cf342dab9753"
    azdev test --live --lf --no-exitfirst
    azdev test --live --lf --no-exitfirst --series
    az account set -s "5e87627b-4ffa-4abf-8040-b1103c84a2fd"
    azdev test --live --lf --no-exitfirst
    azdev test --live --lf --no-exitfirst --series
    az account set -s "6898adc8-5045-473d-a1bf-7012564f43cb"
    azdev test --live --lf --no-exitfirst
    azdev test --live --lf --no-exitfirst --series
    azdev test --no-exitfirst
)
