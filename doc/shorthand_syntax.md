Azure CLI Shorthand Syntax (Preview)
======

Azure cli shorthand syntax can help cli users to pass complicated argument values. 

# Structure Parameter

## Full Value

Shorthand syntax for full value is json without double quotas.
For example if you want to pass following object in --contact argument:

Json:
```json
{
  "name": "Bill",
  "age": 20,
  "paid": true,
  "emails": [
    "Bill@microsoft.com",
    "Bill@outlook.com"
  ],
  "address": {
    "country": "USA",
    "company": "Microsoft",
    "details": {
      "line1": "15590 NE 31st St",
      "line2": "Redmond, WA"
    }
  }
}
```

Shorthand in both powershell and bash:
```bash
az some-command --contact "{name:Bill,age:20,paid:true,emails:[Bill@microsoft.com,Bill@outlook.com],address:{country:USA,company:Microsoft,details:{line1:'15590 NE 31st St',line2:'Redmond, WA'}}}"
```

In the example above you can see the shorthand syntax wrapped in double quotas to make sure the value passed as string in both powershell and bash.
Please don't use single quota to wrap the shorthand syntax, because single quota are used in shorthand to wrap special value with special characters such as space, ':', ',' etc.


## Partial Value

Shorthand syntax for partial value is composed of two parts joined by `=`: the index key and the value. It's format is `{key}={value}`

The value can be simple string, full value format, json or even json file path.

For the above example, if we want to pass some part properties of --contact:


Partial Value for `name` properties
```bash
az some-command --contact name=Bill
```

Partial Value for both `age` and `paid` properties
```bash
az some-command --contact age=20 paid=true
```

Partial Value for second value of `emails`
```bash
az some-command --contact emails[1]="Bill@outlook.com"
```

Partial Value for `details` property of `address`.
```bash
az some-command --contact address.details="{line1:'15590 NE 31st St',line2:'Redmond, WA'}"
```

It's also possible to pass json file as value.
```bash
az some-command --contact address.details=./address_detials.json
```

## 'null' Value

## use '??' to show help

# Single Quotation Expression

## escape character `/`
