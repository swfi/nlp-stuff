import theano
import numpy as np
import math, pdb, sys
import pandas
from ggplot import *


def runGradienDescent(trainingRate, lang1_vectors_filename, lang2_vectors_filename):
    xDF = pandas.read_table(lang1_vectors_filename, sep = " ")
    zDF = pandas.read_table(lang2_vectors_filename, sep = " ")

    vecSize = 400

	x = theano.tensor.fvector('x')
	z = theano.tensor.fvector('z')

	wMatrix = np.asmatrix(np.random.rand(vecSize,vecSize), dtype=np.float64) #, dtype=np.float32
	W = theano.shared(wMatrix, 'W')#, type=theano.tensor.fmatrix)

	transformedVector = theano.tensor.dot(W, x)
	differenceVector = transformedVector - z

	cost = theano.tensor.dot(differenceVector, differenceVector)
	gradients = theano.tensor.grad(cost, [W])
	theano.pp(gradients[0])

	W_updated = W - (trainingRate * gradients[0])
	updates = [(W, W_updated)]

	f = theano.function([x, z], cost, updates=updates, mode='FAST_RUN')

	print "Initial weight matrix:"
	print W.get_value()
	print "\n\n\n\n"

	costVals = []
	idxs = range(5000)
	for outerIteration in range(20):
		currPermutation = np.random.permutation(idxs)
		print >> sys.stderr, "OUT ITERATION:", outerIteration
		progIdx = 0
		permIdx = 0
		currCost = 0
		while permIdx < len(currPermutation) and currCost < 1E40:
			if progIdx % 10 == 0:
				print >> sys.stderr, "PROGRESS:", progIdx
			progIdx += 1

			listIdx = currPermutation[permIdx]

			curr_x = xDF.iloc[listIdx].astype("float32").tolist()[1:]
			curr_z = zDF.iloc[listIdx].astype("float32").tolist()[1:]

			costVal = f(curr_x, curr_z).tolist()
			currCost = costVal
			if costVal > 1E40:
				print >> sys.stderr, "Score too high!"
			costVals.append(costVal)
			permIdx += 1
		print currCost
	#	print W.get_value()
	#	print "======================================="

	actualIterations = range(len(costVals))

	iterationsSeries = pandas.Series(actualIterations)
	costSeries = np.log10(pandas.Series(costVals))
	costDF = pandas.DataFrame(iterationsSeries, columns=["i"])
	costDF["cost"] = costSeries

	p = ggplot(aes(x='i', y='cost'), data=costDF) + geom_line() + ylim(-50,50)
	outfileName = "CostValue_%d_%0.6f.png" % (vecSize, trainingRate)
	p.save(outfileName)

	print "Final weight matrix:"
	print W.get_value()

        pandas.DataFrame(W.get_value()).to_csv("TranslationMatrix_en2sv_%0.6f.txt" % trainingRate, sep=" ")

	return costVals[-1]


runGradienDescent(0.0005, sys.argv[1], sys.argv[2])
