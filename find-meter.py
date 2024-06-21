import os

def findAllFile(base):
    for root, ds, fs in os.walk(base):
        for f in fs:
            fullname = os.path.join(root, f)
            yield fullname

def main():
    base = 'D:\HDI\HDI-meterID-verfied\HDInsight'
    for i in findAllFile(base):
        print(i)

if __name__ == '__main__':
    main()