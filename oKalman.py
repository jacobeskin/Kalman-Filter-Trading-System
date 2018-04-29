
# Import numerical libraries
import numpy as np

class KalmanCoint:

    """
    The state space equations are 
    
    x(t) = Ax(t-1)+w
    z(t) = Hx(t)+v

    where x is the hidden state and z is the observation and w ~ N(0,Q) and 
    v ~ N(0,R). Dimensions are as follows:

    x = [beta alpha]', i.e column vector where beta is the vector familiar from 
                       regression analysis and alpha is the intercept- Length n.
    Q and A are nxn matricies

    z has the dimenstion m and R is mxm

    H = [explanatory_variables 1], it is in general mxn

    The algorith goes as follows (^ denotes the prior dostribution):

    1. Update/initialize the prior expectation from posterior expectation: 
       x^(t) = A*x(t-1)
    2. Update/initialize the prior error from posterior error: 
       P^(t) = A*P(t-1)*A' + Q
    2B. Update H(t) as well if it is dependent on time, as it is here.
    3. Calculate the Kalman gain K(t):
       K(t) = P^(t)*H(t)'*(H(t)*P^(t)*H(t)' + R)**(-1), 
    4. Update the posterior expectation using the observation z(t):
       x(t) = x^(t) + K(t)*(z(t)-H(t)*x^(t))
    5. Update the posterior error (variance):
       P(t) = (I-K(t)*H(t)=*P^(t), where I is the identity matrix

    rinse and repeate.....

    The observation and H(t) are passed into the filtering method at every
    step, all other data is initialized in the beginning. All variables passed 
    into this class must be numpy arrays of the correct dimension!!!
    """

    # Initially what are needed are x_0, P_0, A, Q and R.
    # x_0 has to be of the shape np.array([[1],[1],[1]])
    def __init__(self, x_0, P_0, A, Q, R):

        self.A, self.Q, self.R = A, Q, R
        self.x_pos = x_0
        self.P_pos = P_0

    # Filtering, takes in the observation as well as H.
    # H has to be of the shape np.array([[1,2,3]])
    def Filtering(self, z, H):
        
        # Step 1 and 2 
        self.x_pri = np.matmul(self.A,self.x_pos)
        self.P_pri = np.matmul(self.A,np.matmul(
            self.P_pos,np.transpose(self.A)))+self.Q

        # Steps 2B and 3
        x = np.matmul(H,np.matmul(self.P_pri,np.transpose(H)))+self.R
        if len(x.shape)==0: # m==1
            self.K = np.matmul(self.P_pri,np.transpose(H))*(1.0/float(x))
        else:  # m>1, for generality
            self.K = np.matmul(self.P_pri,np.matmul(
                np.transpose(H),np.linalg.inv(x)))
        
        # Step 4
        if z.size==1: # m==1
            self.x_pos = self.x_pri+self.K*(z-np.matmul(H,self.x_pri))
        else: # m>1, for generality
            self.x_pos = self.x_pri+np.matmul(
                self.K,z-np.matmul(H,self.x_pri))

        # Step 5
        self.P_pos = np.matmul(np.eye(len(self.P_pri))-np.matmul(self.K,H),
                                   self.P_pri)
   
        #return(self.x_pri, self.P_pri)

    
