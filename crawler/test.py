a = raw_input()
nums = []
for i in a.split():
  i = int(i)
  if i>=-40 and i=<40:
    nums.append(i)
  else: 
    print('erro')
print sum(nums)



# coding=utf-8
list1=raw_input().split(" ")
list2=[]
for i in list1:
    if -40<=int(i)<=40:
        a=int(i)
        list2.append(a)
print sum(list2)