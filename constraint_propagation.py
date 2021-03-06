'''
    Solve sudoku using constraint propagation with naken twin strategy
'''
import random
import numpy as np
from generator import Generator
import sys
import time
from BackTrack import BackTrack


GENERATOR = Generator(np.zeros((9, 9)))
class Solve:
    '''
        generate the problem sudoku and then solve it with naked twin technique
    '''
    def __init__(self, number_of_missing_values):
        '''
            number_of_missing_values : number of values missing in the problem sudoku
            sample_size : define the allowed number of population
        '''
        #Generate a solution matrix
        self.solution = GENERATOR.solution_matrix()
        #create the problem matrix by removing the fields
        self.problem = GENERATOR.problem_matrix(number_of_missing_values)
        #identify the missing values position
        self.position = GENERATOR.position(self.problem)
        self.number_of_missing_values = number_of_missing_values
        self.domain= {}
        #print(self.problem)
    def __initialDomain(self):
        '''
            generate a intial dictionary with positions of missing values as key and possible values array 
        '''
        for pos in self.position:
                if len(self.domain.get(pos[0], {})) == 0:
                    self.domain[pos[0]]= {}
                self.domain[pos[0]][pos[1]] = [1,2,3,4,5,6,7,8,9]

    def __assign_value__(self,row,col):
        '''
            get possible values for the position
        '''
       
        val = self.domain[row][col]
        val = list(set(val) - set (self.problem[row,:]))
        val = list(set(val) - set (self.problem[:,col]))
        r = 3 * int(row / 3)
        c = 3 * int(col / 3)
        val = list(set(val) - set (self.problem[r:r+3,c:c+3].flatten()))
        return val

    def __generateDomain__(self):
        '''
            generate dictionary for of position with possible values
        '''
        if len (self.domain) == 0:
            self.__initialDomain()
        for row in self.domain:
            for col in self.domain[row]:
                self.domain[row][col] = self.__assign_value__(row,col)

    def __oneReduceContraint__(self):
        '''
            if domain has single value, add that to problem matrix
            returns number of position filled
        '''
        count= 0
        for row in list(self.domain):
            for col in list(self.domain[row]):
                if len(self.domain[row][col])==1 : 
                    #print(list(self.domain[row][col])[0])
                    self.problem[row][col]= list(self.domain[row][col])[0]
                    count = count +1
                    del self.domain[row][col]
                    #print(self.position,self.position== [row, col],)
                    #np.delete(self.position,np.where(self.position==[row,col])[0][0], axis=0)
        return count
    def __twinReduceContraint__(self):
        '''
            check if a twin exist in the domain
        '''
        count = 0
        for row in self.domain:
            for col in self.domain.get(row, {}):
                if len(self.domain[row][col]) == 2:
                    isTwin = self.__searchTwin__(row,col)
                    if len(isTwin) !=0:
                        count = count + self.remove_twin_from_relations([row,col], isTwin)
        return count
    def __searchTwin__(self,row,col):
        '''
            search if twin exist for the position
        '''
        for i in range(9):
            if i in self.domain[row]:
                if  i != col and set(self.domain[row][col]) == set(self.domain[row][i]):
                    return [row , i]
            if i in self.domain and col in self.domain[i]:
                if i !=row and  set(self.domain[row][col]) == set(self.domain[i][col]) :
                    return [i, col]
        r = 3 * int(row / 3)
        c = 3 * int(col / 3)
        for r in range(r, r+3):
            for c in range(c,c+3):
                if [r,c] != [row,col] and  c in self.domain.get(r,{}) and set(self.domain[row][col]) == set(self.domain[r][c]):
                    return [r,c]
        return []
    def remove_twin_from_relations(self, one, two):
            '''
                reduce domain size if twin values exist anywhere else
            '''
            count =0 
            #is one and two in same row ? 
            if one[0] == two[0]:
                for i in range(9):
                        if i != one[1] and i != two[1] and i in self.domain.get(one[0],{}):
                            earlier = len(self.domain[one[0]][i])
                            if earlier !=2:
                                self.domain[one[0]][i] = list(set(self.domain[one[0]][i]) - set (self.domain[one[0]][one[1]]))
                            if earlier > len(self.domain[one[0]][i]):
                                count= count +1
            #is one and two in same column ?  
            elif one[1] == two[1]:
                for i in range(9):
                    if i != one[0] and i !=two[0] and i in self.domain:
                        if one[1] in self.domain[i]:
                            earlier = len(self.domain[i][one[1]])
                            if earlier !=2:
                                self.domain[i][one[1]] = list(set(self.domain[i][one[1]]) - set(self.domain[one[0]][one[1]]))
                            if earlier > len(self.domain[i][one[1]]):
                                count= count +1
            #one and two in same box
            if one != two or [3 * int(one[0]/3), 3 * int(one[1]/3) ] ==  [3 * int(two[0]/3), 3 * int(two[1]/3) ]:
                r = 3 * int(one[0]/3)
                c = 3 * int(one[1]/3)
                for r1 in range(r, r+3):
                    for c1 in range (c,c+3):
                        if c1 in  self.domain.get(r1,{}) and [r1,c1] != one and [r1,c1] !=two:
                            earlier = len(self.domain[r1][c1])
                            if earlier !=2:
                                self.domain[r1][c1] = list(set(self.domain[r1][c1]) - set(self.domain[one[0]][one[1]]))
                            if earlier >  len(self.domain[r1][c1]) :
                                count= count +1
            return count
    def filterDomain(self):
        '''
            remove rows where all column are done  in dictionary 
            return a position matrix for backtracking
        '''
        position = []
        for r in list(self.domain):
            for c in list(self.domain[r]):
                if len(self.domain[r][c]) != 0:
                    #del self.domain[r][c]
                #else:
                    position.append([r,c])
            if len(self.domain[r]) == 0: 
                del self.domain[r]
        return position
    def getSolution(self):
        '''
            use the methods in sequence to generate the solution
        '''
        count = 0
        ITERATE = 0
        self.__generateDomain__()
        #print("step: generate domain\n", self.domain )
        while self.__oneReduceContraint__() !=0:
            self.__oneReduceContraint__()
            self.__generateDomain__()
            #print("one reduced", iterate, "\n", self.domain)
            #sys.stdin.readlines()
            ITERATE = ITERATE +1 
        
        count = count + self.__twinReduceContraint__()
        #print("twin reduced", count, "\n", self.domain)
        if count !=0:
            #print(count,"\n",self.problem,"\n",self.position,"\n",self.domain)
            #sys.stdin.readlines()
            ITERATE  = ITERATE  + self.getSolution()
            return ITERATE
        else:
            #check how many positions are left. 
            #print("before filter\n",self.domain, "\n before backTrack\n", self.problem)
            #position = self.filterDomain() 
            out= BackTrack(self.problem)
            output , count= out.do()
            
            #print ("filter domain",self.domain,"\n",self.problem, "\noutput:\n", output)
            return ITERATE + count
    def onlyBackTrack(self):
        '''
            iteratively put a value to a position and proceed until final solution is achived
        '''
        out = BackTrack(self.problem)
        output,count = out.do()
        return count

    def checkSolution(self):
        '''
            match if solution and problem are same matrix
        '''
        if np.array_equal(self.problem, self.solution):
            return True
        else:   
            return False

problem_size = [10,15,20,25,30,35,40,45,50,55,60]
repeat = 10
data = np.zeros(( len(problem_size)*repeat,5),dtype=int)
pointer = 0
for i in problem_size :
    for  j in range(repeat):
        data[pointer][0] = i
        SOL=Solve(i)
        start_time = time.time()
        back_iteration = SOL.onlyBackTrack()
        data[pointer][1] = back_iteration
        data[pointer][2] = int((time.time() - start_time)*1000)

        start_time = time.time()
        contraint_iteration = SOL.getSolution()
        data[pointer][3] =  contraint_iteration
        data[pointer][4] =  int((time.time() - start_time)*1000)
        pointer = pointer+1
        print (data[pointer-1])
print(data)
np.savetxt("calculation.csv", data, delimiter=",", fmt= '%10.5f' )
