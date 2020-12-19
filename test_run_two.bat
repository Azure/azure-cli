FOR /L %%x IN (1,1,1) DO (
    azdev test --no-exitfirst
    azdev test --live --lf --no-exitfirst
)
