import numpy as np
from scipy.optimize import curve_fit
from scipy import asarray
import matplotlib.pyplot as plt

y = [33.0, 112.0, 122.0, 133.0, 114.0, 108.0, 70.0, 147.0, 63.0, 54.0, 146.0, 100.0, 75.0, 137.0, 65.0, 49.0, 70.0, 38.0, 67.0, 91.0, 104.0, 47.0, 52.0, 118.0, 135.0, 61.0, 47.0, 34.0, 117.0, 141.0, 74.0, 77.0, 61.0, 54.0, 53.0, 109.0, 85.0, 36.0, 84.0, 141.0, 98.0, 96.0, 92.0, 72.0, 33.0, 70.0, 60.0, 125.0, 56.0, 50.0, 58.0, 181.0, 81.0, 55.0, 109.0, 60.0, 57.0, 53.0, 34.0, 57.0, 45.0, 34.0, 69.0, 90.0, 29.0, 35.0, 103.0, 76.0, 84.0, 68.0, 73.0, 34.0, 75.0, 99.0, 82.0, 107.0, 129.0, 128.0, 150.0, 485.0, 786.0, 1379.0, 1524.0, 2052.0, 2421.0, 1737.0, 905.0, 333.0, 239.0, 177.0, 140.0, 149.0, 125.0, 102.0, 106.0, 114.0, 82.0, 54.0, 25.0, 50.0, 44.0, 34.0, 61.0, 61.0, 73.0, 60.0, 66.0, 63.0, 29.0, 43.0, 55.0, 59.0, 39.0, 29.0, 26.0, 33.0, 38.0, 48.0, 39.0, 29.0, 35.0, 55.0, 30.0, 49.0, 55.0, 27.0, 74.0, 70.0, 96.0, 38.0, 63.0, 90.0, 92.0, 46.0, 67.0, 29.0, 70.0, 78.0, 34.0, 68.0, 72.0, 40.0, 56.0]
x = range(len(y))

x = asarray(x)
y = asarray(y)

print('x:', x)
print('y:', y)

n = len(x)						  #the number of data
mean = sum(x*y)/n				   #note this correction
sigma = sum(y*(x-mean)**2)/n		#note this correction

def myGaussian(x, amplitude, mean, stddev):
	return amplitude * np.exp(-((x - mean) / 4 / stddev)**2)

popt,pcov = curve_fit(myGaussian,x,y)

# popt has (amplitude, mean, sd), I think?

print('popt:', popt)
print('pcov:', pcov)

# now get FWHM from fit
# see: https://stackoverflow.com/questions/10582795/finding-the-full-width-half-maximum-of-a-peak
fit_amp, fit_mu, fit_stdev = popt
FWHM = 2*np.sqrt(2*np.log(2))*fit_stdev
print('FWHM:', FWHM)

# this seems to work really well !!!
def FWHM(X,Y):
	half_max = max(Y) / 2.
	#find when function crosses line half_max (when sign of diff flips)
	#take the 'derivative' of signum(half_max - Y[])
	d = np.sign(half_max - asarray(Y[0:-1])) - np.sign(half_max - asarray(Y[1:]))
	#plot(X[0:len(d)],d) #if you are interested
	#find the left and right most indexes
	left_idx = np.where(d > 0)[0]
	right_idx = np.where(d < 0)[-1]
	return X[right_idx] - X[left_idx] #return the difference (full width)

print('FWHM2:', FWHM(x,y)
)
plt.plot(x,y,'b+:',label='data')
plt.plot(x,myGaussian(x,*popt),'ro:',label='fit')
plt.legend()
plt.show()
