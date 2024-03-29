from builtins import range
from builtins import object
import numpy as np

from NN.layers import *
from NN.layer_utils import *


class TwoLayerNet(object):
    """
    A two-layer fully-connected neural network with ReLU nonlinearity and
    softmax loss that uses a modular layer design. We assume an input dimension
    of D, a hidden dimension of H, and perform classification over C classes.

    The architecure should be affine - relu - affine - softmax.

    Note that this class does not implement gradient descent; instead, it
    will interact with a separate Solver object that is responsible for running
    optimization.

    The learnable parameters of the model are stored in the dictionary
    self.params that maps parameter names to numpy arrays.
    """

    def __init__(self, input_dim=3*32*32, hidden_dim=100, num_classes=10,
                 weight_scale=1e-3, reg=0.0):
        """
        Initialize a new network.

        Inputs:
        - input_dim: An integer giving the size of the input
        - hidden_dim: An integer giving the size of the hidden layer
        - num_classes: An integer giving the number of classes to classify
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - reg: Scalar giving L2 regularization strength.
        """
        self.params = {}
        self.reg = reg
        self.params['W1'] = np.random.normal(scale=weight_scale,size=(input_dim, hidden_dim))
        self.params['b1'] = np.zeros(hidden_dim)
        self.params['W2'] = np.random.normal(scale=weight_scale,size=(hidden_dim,num_classes))
        self.params['b2'] = np.zeros(num_classes)



    def loss(self, X, y=None):
        """
        Compute loss and gradient for a minibatch of data.

        Inputs:
        - X: Array of input data of shape (N, d_1, ..., d_k)
        - y: Array of labels, of shape (N,). y[i] gives the label for X[i].

        Returns:
        If y is None, then run a test-time forward pass of the model and return:
        - scores: Array of shape (N, C) giving classification scores, where
          scores[i, c] is the classification score for X[i] and class c.

        If y is not None, then run a training-time forward and backward pass and
        return a tuple of:
        - loss: Scalar value giving the loss
        - grads: Dictionary with the same keys as self.params, mapping parameter
          names to gradients of the loss with respect to those parameters.
        """
        scores = None
        out_1,cache_1 = affine_relu_forward(X,self.params['W1'],self.params['b1'])
        out_2,cache_2 = affine_forward(out_1,self.params['W2'],self.params['b2'])
        scores = out_2
        if y is None:
            return scores

        loss, grads = 0, {}
        loss, dscores = softmax_loss(scores, y)
        loss += 0.5*self.reg*np.sum(self.params['W1']**2) + 0.5*self.reg*np.sum(self.params['W2']**2)

        dx_2, grads['W2'], grads['b2'] = affine_backward(dscores, cache_2)
        dx_1, grads['W1'], grads['b1'] = affine_relu_backward(dx_2, cache_1)

        grads['W2'] += self.reg*self.params['W2']
        grads['W1'] += self.reg*self.params['W1']

        return loss, grads


class FullyConnectedNet(object):
    """
    A fully-connected neural network with an arbitrary number of hidden layers,
    ReLU nonlinearities, and a softmax loss function. This will also implement
    dropout and batch/layer normalization as options. For a network with L layers,
    the architecture will be

    {affine - [batch/layer norm] - relu - [dropout]} x (L - 1) - affine - softmax

    where batch/layer normalization and dropout are optional, and the {...} block is
    repeated L - 1 times.

    Similar to the TwoLayerNet above, learnable parameters are stored in the
    self.params dictionary and will be learned using the Solver class.
    """

    def __init__(self, hidden_dims, input_dim=3*28*28, num_classes=10,
                 dropout=1, normalization=None, reg=0.0,
                 weight_scale=1e-2, dtype=np.float32, seed=None):
        """
        Initialize a new FullyConnectedNet.

        Inputs:
        - hidden_dims: A list of integers giving the size of each hidden layer.
        - input_dim: An integer giving the size of the input.
        - num_classes: An integer giving the number of classes to classify.
        - dropout: Scalar between 0 and 1 giving dropout strength. If dropout=1 then
          the network should not use dropout at all.
        - normalization: What type of normalization the network should use. Valid values
          are "batchnorm", "layernorm", or None for no normalization (the default).
        - reg: Scalar giving L2 regularization strength.
        - weight_scale: Scalar giving the standard deviation for random
          initialization of the weights.
        - dtype: A numpy datatype object; all computations will be performed using
          this datatype. float32 is faster but less accurate, so you should use
          float64 for numeric gradient checking.
        - seed: If not None, then pass this random seed to the dropout layers. This
          will make the dropout layers deteriminstic so we can gradient check the
          model.
        """
        self.normalization = normalization
        self.use_dropout = dropout != 1
        self.reg = reg
        self.num_layers = 1 + len(hidden_dims)
        self.dtype = dtype
        self.params = {}
        
        all_dims = [input_dim] + hidden_dims + [num_classes]
        for i in range (0, self.num_layers):
            W_name = 'W'+str(i+1)
            b_name = 'b'+str(i+1)
            if self.normalization=='batchnorm' and (i!= self.num_layers-1):
                gamma_name = 'gamma' + str(i+1)
                beta_name = 'beta' + str(i+1)
                self.params[gamma_name] = np.ones(all_dims[i])
                self.params[beta_name] = np.zeros(all_dims[i])
            self.params[b_name] = np.zeros(all_dims[i+1])
            self.params[W_name] = np.random.normal(scale=weight_scale, size=(all_dims[i],all_dims[i+1]))
            
        self.dropout_param = {}
        if self.use_dropout:
            self.dropout_param = {'mode': 'train', 'p': dropout}
            if seed is not None:
                self.dropout_param['seed'] = seed

        self.bn_params = []
        if self.normalization=='batchnorm':
            self.bn_params = [{'mode': 'train'} for i in range(self.num_layers - 1)]
        if self.normalization=='layernorm':
            self.bn_params = [{} for i in range(self.num_layers - 1)]

        # Cast all parameters to the correct datatype
        for k, v in self.params.items():
            self.params[k] = v.astype(dtype)


    def loss(self, X, y=None):
        """
        Compute loss and gradient for the fully-connected net.

        Input / output: Same as TwoLayerNet above.
        """
        X = X.astype(self.dtype)
        mode = 'test' if y is None else 'train'

        if self.use_dropout:
            self.dropout_param['mode'] = mode
        if self.normalization=='batchnorm':
            for bn_param in self.bn_params:
                bn_param['mode'] = mode
        scores = None
        pass
        self.cache = {}
        self.dropout_cache = {}
        self.batchnorm_cache = {}
        N = X.shape[0]
        D = np.prod(X.shape[1:])
        x2 = X.reshape(N,D)
        scores = x2
        
        for i in range(1,self.num_layers+1):
            id_str = str(i)
            W_name = 'W' + id_str
            b_name = 'b' + id_str
            gamma_name = 'gamma' + id_str
            beta_name = 'beta' + id_str
            batchnorm_name = 'batchnorm' + id_str
            dropout_name = 'dropout' + id_str
            cache_name = 'c' + id_str
            
            if i == self.num_layers:
                scores, cache = affine_forward(scores, self.params[W_name],self.params[b_name])
            else:
                if self.normalization=='batchnorm':
                    scores, self.batchnorm_cache[batchnorm_name] = batchnorm_forward(scores, self.params[gamma_name],self.params[beta_name],self.bn_params[i-1])
                scores, cache = affine_relu_forward(scores, self.params[W_name], self.params[b_name])
                if self.use_dropout:
                    scores, self.dropout_cache[dropout_name] = dropout_forward(scores, self.dropout_param)

            
            self.cache[cache_name] = cache

        if mode == 'test':
            return scores

        loss, grads = 0.0, {}

        loss, der = softmax_loss(scores,y)
        for i in range(self.num_layers,0,-1):
            id_str = str(i)
            W_name = 'W' + id_str
            b_name = 'b' + id_str
            gamma_name = 'gamma' + id_str
            beta_name = 'beta' + id_str
            batchnorm_name = 'batchnorm' + id_str
            dropout_name = 'dropout' + id_str
            cache_name = 'c' + id_str

            loss += 0.5*self.reg*np.sum(self.params[W_name]**2)  # l2 regulation
            if i == self.num_layers:
                der, grads[W_name], grads[b_name] = affine_backward(der, self.cache[cache_name])
            else:
                if self.use_dropout:
                    der = dropout_backward(der,self.dropout_cache[dropout_name])
                der, grads[W_name], grads[b_name] = affine_relu_backward(der, self.cache[cache_name])
                if self.normalization=='batchnorm':
                    der, grads[gamma_name], grads[beta_name] = batchnorm_backward(der, self.batchnorm_cache[batchnorm_name])
            grads[W_name] += self.reg*self.params[W_name]


        return loss, grads
