import numpy as np 
import os

class nnhs():
	log=[]
	def __init__(self,nnhs_file ):
		self.nnhs_file=nnhs_file
		self.name=os.path.basename(nnhs_file)
		try:
			fp = open(nnhs_file, 'r')
		except IOError:
			#print 'cannot open:', nnhs_file 
			print('cannot open:', nnhs_file) 	                             # MH: 20181207 - python 3.0 ney syntax! 
			return
		#print  'net:', os.path.basename(nnhs_file)                             # MH: 20181207 - python 3.0 ney syntax!
		z=fp.readline()
		self.problem=z
		self.input=[]
		self.invar=[]
		self.output=[]
		self.outvar=[]
		while not z.startswith('#'): 
			z=fp.readline()
			if z.startswith('input'):
				self.input.append(z)
				self.invar.append(z.split()[3])
			if z.startswith('output'):
				self.output.append(z)
				self.outvar.append(z.split()[3])
		
		self.ninp=int(fp.readline())
		self.inrange=[]
		for k in range(self.ninp):
			self.inrange.append(fp.readline().split())   #fscanf(fp,'%g',[2 self.in])
		self.inrange=np.array(self.inrange,dtype='float').transpose() 
		
		self.noutp=int(fp.readline())
		self.outrange=[]
		for k in range(self.noutp):
			self.outrange.append(fp.readline().split())    #fscanf(fp,'%g',[2 self.in])
		self.outrange=np.array(self.outrange,dtype='float').transpose()
		
		while not '$' in z: z=fp.readline()   
		planes=fp.readline().split('=')[1].split()        #str2num(r)
		self.nplanes=int(planes[0])
		self.size=map(int, planes[1:])
		self.bias=[] #cell(1,self.nplanes-1)
		for npl in range(self.nplanes-1): #=1: self.nplanes-1
			c=fp.readline().split()  #fscanf(fp,'%s',3)
			h=np.zeros((int(c[2]))) 
			for i in range(int(c[2])):
				h[i]=float(fp.readline())
			self.bias.append(h) #fscanf(fp,'%g',self.size(npl+1))
		
		self.wgt=[] #cell(1,self.nplanes-1)
		for npl in range(self.nplanes-1): #=1: self.nplanes-1
			c=fp.readline().split()  #fscanf(fp,'%s',3)
			h=np.zeros((int(c[3]), int(c[2])) )
			for i in range(int(c[3])):
				for j in range(int(c[2])):
					h[i, j]=fp.readline()
			self.wgt.append(h) #fscanf(fp,'%g',self.size(npl+1))  
		fp.close()
		self.oorange=np.zeros(self.ninp, dtype=np.int)
	
	def ff_nnhs(self,  inp):
		act=(inp-self.inrange[0,:])/(self.inrange[1,:]-self.inrange[0,:])
		for npl in range(self.nplanes-1):
			sum=self.bias[npl]+ np.dot(self.wgt[npl], act)
			# ind=np.nonzero(sum > 10.)
			# sum[ind]=10.
			# ind=np.nonzero(sum < -10.)
			#sum[ind]=-10.
			sum[sum>10]=10.
			sum[sum<-10]=-10.
			act=1./(1.+np.exp(-sum))
		res=act*(self.outrange[1,:]-self.outrange[0,:])+self.outrange[0,:]
		return res
	
#	def info(self):
#		for  inp in self.input:
#			#print inp, 	                                                   # MH: 20181207 - python 3.0 ney syntax!
#			
#		for outp in self.output:
#			#print outp,                                                       # MH: 20181207 - python 3.0 ney syntax!
			
	
	def chk_inp(self, input):
		oor=False
		for i in range(self.ninp):
			if input[i]<self.inrange[0, i] or input[i]>self.inrange[1, i] or np.isnan(input[i]):
				oor=True
				self.oorange[i]+=1
				#self.log.append( 'Warning: ',  self.invar[i], 'out of range!', self.inrange[0, i], '<', input[i], '>', self.inrange[1, i]
				#self.log.append( 'Warning: %s out of range!  %f< %f < %f'%(self.invar[i], self.inrange[0, i],  input[i], self.inrange[1, i]))
		return oor
	
	def OLCI_weighted_oor(self, input):
		weights=np.array([0.1,0.5,0.8,0.8,1,1,1,0.8,0.5,0.5,0.3])
		weights = weights/np.sum(weights)
		oor= 0.
		if np.sum(np.isnan(input)) > 0:
			oor =1.
		else:
			for i in range(self.ninp):
				a = input[i] - self.inrange[0, i]
				b = input[i] - self.inrange[1, i]
				if a < 0:
					oor= oor+ weights[i]*np.abs(a)
				if b > 0:
					oor= oor+ weights[i]*np.abs(b)
				self.oorange[i]+=1
		
		return oor

	def show_oorange(self):
		for i in range(self.ninp):
			#print 'input:',self.invar[i], 'out of range:', self.oorange[i]  
			print('input:',self.invar[i], 'out of range:', self.oorange[i])    # MH: 20181207 - python 3.0 ney syntax!

####################################################################### 
#test
if __name__=='__main__':
    from mpl_toolkits.mplot3d import Axes3D
    import matplotlib.pyplot as plt
    from matplotlib import cm
    
    X=np.arange(-4, 4.1, 0.16)
    Y=np.arange(-4, 4.1, 0.16)
    x, y=np.meshgrid(X,Y)
    
    nn=nnhs('/home/wschoenf/python/nn/10_0.2.net')
    nn.info()
    z=np.zeros((51, 51))
    for l in range(51):
        for m in range(51):
            inp=np.hstack([x[l, m], y[l, m]])
            z[l, m]=nn.ff_nnhs(inp)
            nn.chk_inp(inp)
            
    fig = plt.figure()
    ax = fig.add_subplot(111  ,  projection='3d')
    ax.plot_surface( x, y, z, cmap=cm.jet, rstride=1, cstride=1 )
#    ax.contour( X, Y, z, cmap=cm.jet)
    plt.show()
    #nn=nnhs('25x4x20_22.5.net')
