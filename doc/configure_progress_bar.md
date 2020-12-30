# Progress Bar Usage Guideline

## Prepare Resource
```
az group create -n mygroup -l eastus
```

## Determinate Progress Bar
## Percentage progress bar
![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)

Try:
```
az storage account create -n mystorageaccount -g mygroup
```

## Timing progress bar
![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)

Try:
```
az network lb create -g mygroup -n mylb --sku Basic
```

## Indeterminate Progress Bar
### Pong like progress bar
![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)

Try:
```
az vm create -n myvm -g mugroup --image ubuntults
```

### Spinner progress bar
![Alt Text](https://media.giphy.com/media/vFKqnCdLPNOKc/giphy.gif)

Try:
```
az network lb delete -g mygroup -n mylb
```