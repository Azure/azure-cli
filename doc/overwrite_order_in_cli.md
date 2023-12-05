**Background**  

Now, our command table is loaded three times.
The commands loaded later will override the commands loaded earlier
1. Load the CLI module
2. Load the wheel extension (az extension add)
3. Load dev extension (azdev extension add)  

If modules or extensions are at the same level, they will be loaded in **alphabetical order**, so the modules and extensions loaded later will also override the commands in the modules and extensions loaded earlier.

**What if I want to my preview extension overwrite my GA extension?**

You need to ensure that the extension name of preview is sorted after the extension name of GA
For example：
GA extension name： containerapp
Preview extension name: containerapp-preview

**Testing result**

1. If the command only exists in the ga extension, keep it
![image](https://user-images.githubusercontent.com/18628534/225559734-c4e37f84-7f52-4f32-9bba-85243a3e1b85.png)
2. If the command exists at the same time, the preview command will overwrite ga
![image](https://user-images.githubusercontent.com/18628534/225559840-8523583c-24dd-45eb-aa82-eb8de72d75b3.png)
3. If the command only exists in the preview extension, keep it
![image](https://user-images.githubusercontent.com/18628534/225559911-dae4ec3b-dbe4-4fb6-a612-f6e7af814bf8.png)