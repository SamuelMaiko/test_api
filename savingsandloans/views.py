from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .serializers import SavingsAccountSerializer, SavingsItemSerializer, SavingsTransactionSerializer,LoanRequestSerializer, LoanTransactionSerializer, CustomUserSerializer
from rest_framework import status, generics
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from newmamapesa.models import Loan, Savings, SavingsItem, Item, LoanTransaction
from .serializers import LoanRequestSerializer, LoanTransactionSerializer
from decimal import Decimal
from .signals import after_deposit, after_repay_loan, loan_disbursed
from .serializer_helpers import get_all_transactions

class SavingsAccountView(APIView):
    """
    API endpoint for retrieving savings accounts.
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user=request.user
        # Retrieve the savings account associated with the authenticated user
        savings_account=get_object_or_404(Savings, user=user)
        serializer=SavingsAccountSerializer(savings_account)
        # Return the serialized data as JSON response
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)

class SavingsItemsView(APIView):
    """
    API endpoint for retrieving the items a user is saving towards
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user=request.user
        # retrieving the savings items associated to a user's savings account
        all_savings_items=SavingsItem.objects.filter(savings=user.savings_account)
        
        serializer=SavingsItemSerializer(all_savings_items, many=True)
        
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)

class SavingsItemView(APIView):
    """
    API endpoint for retrieving a specific saving item by id
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request, id):
        user=request.user
        condition1={'savings':user.savings_account}
        condition2={'id':id}
        #filtering the savings item belonging to user's savings account and by id 
        specific_savings_item=SavingsItem.objects.filter(**condition1, **condition2)
        # incase user wants to access another user's savings item
        if specific_savings_item:
            response_dict=dict(error="Resource not found")
            return Response(response_dict, status=status.HTTP_404_NOT_FOUND)
        
        serializer=SavingsItemSerializer(specific_savings_item)        
        return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)
class DepositSavingsView(APIView):
    """
    API endpoint for depositing into a specific savings item
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, saving_item_id):
        user=request.user
        specific_save_item=get_object_or_404(SavingsItem, id=saving_item_id)
        # checking if saving item belong to the user
        if specific_save_item.savings.user==user:
            deposit_amount=request.data.get("deposit_amount")
            phone_number=request.data.get("phone_number")
            amount=request.data.get("amount")
            # payment method id
            payment_method=request.data.get("payment_method")
            # if payment_method not provided default to 1
            if not payment_method:
                payment_method=1
            
            if phone_number and amount:
                pass
                # handle payment here
            
            if deposit_amount:
                # add the deposited amount to the amount saved
                specific_save_item.amount_saved+=deposit_amount
                specific_save_item.save()
                # send signal to create transaction
                after_deposit.send(sender=None, payment_method=payment_method, amount=deposit_amount, savings_item=saving_item_id, type="deposit")
                response_dict=dict(message="Deposit successful")
                return JsonResponse(response_dict, status=status.HTTP_202_ACCEPTED)
            else:
                response_dict=dict(error="Provide the deposit amount")
                return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            response_dict=dict(error="Sorry the requested resource could not be found")
            return JsonResponse(response_dict, status=status.HTTP_404_NOT_FOUND)

class CreateSavingsView(APIView):
    """
    API endpoint for creating a new savings item
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]  
    def post(self, request):
        received_item_name=request.data.get("item_name")
        received_item_price=request.data.get("item_price")
        saving_period=request.data.get("saving_period")
        phone_number=request.data.get("phone_number")
        initial_deposit=request.data.get("initial_deposit")
      
        # handle payment here   
        if phone_number and initial_deposit:
            pass
        # start creation process if received item name and price exist
        if received_item_name and received_item_price:
            #  REASON: no Items available from supplier for now, CREATE an item and associate it with the user's savings
            new_item=Item(name=received_item_name, price=received_item_price)
            new_item.description=f"An item called {received_item_name}"
            new_item.save()
            user=request.user
            #associating item to a SavingsItem instance 
            new_savings_item=SavingsItem(item=new_item, savings=user.savings_account)
            new_savings_item.target_amount=received_item_price
            # if saving period provided use it ELSE use the database default
            if saving_period:
                new_savings_item.saving_period=saving_period
            new_savings_item.save()
            response_dict=dict(message="Item added successfully to savings items!!")
            # returning created savings Item to user
            response_dict["saving_item"]=dict(name=new_savings_item.item.name, start_date=new_savings_item.start_date, end_date=new_savings_item.due_date, duration=new_savings_item.saving_period)
            return JsonResponse(response_dict, status=status.HTTP_201_CREATED)
        else:
            response_dict=dict(message="Please provide the necessary data i.e item_name, item_price")
            return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)
            
            
class ChangeSavingsPeriodView(APIView):
    """
    API endpoint for changing the savings period od savings item
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, saving_item_id):
        new_savings_period=request.data.get("new_savings_period")
        # if savings period provided
        if new_savings_period:
            user=request.user 
            specific_savings_item=get_object_or_404(SavingsItem, id=saving_item_id) 
            # verify if savings item belongs to the current user
            if specific_savings_item.savings.user==user:
                previous_end_date=specific_savings_item.due_date
                specific_savings_item.saving_period=new_savings_period
                specific_savings_item.save()
                
                response_dict=dict(message="Successfully updated savings period")
                # returning the changes as response
                response_dict["item"]=dict(name=specific_savings_item.item.name, price=specific_savings_item.item.price)
                response_dict["previous_end_date"]=previous_end_date
                response_dict["new_end_date"]=specific_savings_item.due_date   
                return JsonResponse(response_dict, status=status.HTTP_200_OK)
            # handle response if savings item does not belong to user
            else:
                response_dict=dict(message="The resource could not be found")
                return JsonResponse(response_dict, status=status.HTTP_404_NOT_FOUND)
        #if savings period not provided   
        else:
            response_dict=dict(message="Please provide the necessary data i.e new_savings_period ")
            return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)

class SavingsTransactionsView(APIView):
    """
    API endpoint for retrieving transactions of a user
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]  
    def get(self, request):
        user=request.user
        all_savings_items=SavingsItem.objects.filter(savings=user.savings_account)
        # calling function to get transactions
        all_transactions=get_all_transactions(all_savings_items)
        # if there are transactions
        if all_transactions:
            serializer=SavingsTransactionSerializer(all_transactions, many=True)
            return JsonResponse(serializer.data, safe=False, status=status.HTTP_200_OK)   
        else:
            response_dict=dict(message="No transactions")
            return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)   
            

class WithdrawSavingsToSupplier(APIView):
    """
    API endpoint for withdrawing to supplier till after savings target reached
    """
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request, saving_item_id):
        # getting specific savings item to withdraw from
        specific_savings_item=get_object_or_404(SavingsItem, id=saving_item_id)
        
        supplier_till=request.data.get("supplier_till")
        amount=request.data.get("withdraw_amount")  # optional
        # handle if supplier till provided
        if supplier_till:
            # prevent user from using app money, only used amount saved
            if amount:
                if Decimal(amount)>specific_savings_item.amount_saved:
                    response_dict=dict(message="Not enough funds in account")
                    return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
            
            payment_successful=False 
            
            # handle payment through gateway
            
            
            # end of success payment
            payment_successful=True 
            # to enable user to withdraw ONLY after the TARGET amount is reached, payment successful
            if specific_savings_item.is_target_amount_reached and payment_successful and specific_savings_item.in_progress:
                specific_savings_item.in_progress=False
                specific_savings_item.save()
                
                if amount:
                    amount_paid_to_till=Decimal(amount)
                # if amount not provided, use target_amount for the savings item 
                if not amount:
                    amount_paid_to_till=specific_savings_item.target_amount
                    
                specific_savings_item.amount_saved-=amount_paid_to_till
                specific_savings_item.save()
                
                response_dict=dict(message="Withdrawal successful to supplier")
                return JsonResponse(response_dict, status=status.HTTP_200_OK)
            # if target amount not REACHED 
            else:
                if specific_savings_item.in_progress:
                    response_dict=dict(message="Target amount not reached")
                    return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)
                 
                # handle if savings is done (i.e in_progress=False) to withdraw extra funds 
                # It was toggled to in_progress=False when the savings target amount reached AND PAID to supplier
                else:
                    # if extra funds to be withdrawn are available in account
                    if amount:
                        if Decimal(amount)>specific_savings_item.amount_saved:
                            response_dict=dict(message="Not enough funds in account")
                            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)      
                        else:
                            payment_successful=False
                            # handle payment of extra funds to gateway
                            
                            payment_successful=True
                            
                                
                            if payment_successful:
                                specific_savings_item.amount_saved-=amount
                                specific_savings_item.save()
                                
                                response_dict=dict(message="Withdrawal of extra funds successful")
                                return Response(response_dict, status=status.HTTP_200_OK)                                
        
        # handle if supplier till not provided
        else:
            response_dict=dict(error="supplier till not provided")
            return JsonResponse(response_dict, status=status.HTTP_400_BAD_REQUEST)
            
        
class LoanRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LoanRequestSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = request.user
            amount_requested = Decimal(serializer.validated_data['amount'])
            
            if amount_requested>0:
            
                eligibility_check = self.check_loan_eligibility(user, amount_requested)

                if eligibility_check['is_eligible']:
                    
                    loan = Loan(
                        user=user,
                        amount=amount_requested,                    
                    )

                    loan.save()
                    # AMOUNT TO GO TO PAYMENT GATEWAY
                    amount_to_disburse=loan.amount_disbursed
                    print(amount_to_disburse)
                    # After successful payment
                    loan_disbursed.send(sender=None, amount=amount_to_disburse, user=user, loan=loan)

                    return Response({"message": "Loan request successful.", 'amount': amount_requested}, status=status.HTTP_201_CREATED)
                else:
                    return Response({"error": eligibility_check['error']}, status=status.HTTP_400_BAD_REQUEST)
                
            else:
                response_dict=dict(message="Amount not provided")
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def check_loan_eligibility(self, user, amount_requested):
        # Business logic for checking loan eligibility
        condition_1 = user.is_eligible
        # condition_2 = user.loan_owed <= 8000
        condition_3 = amount_requested <= user.amount_borrowable      
        if not condition_1:
            return {'is_eligible': False, 'error': "Loan limit exhausted."}
        # elif not condition_2:
        #     return {'is_eligible': False, 'error': "Loan owed exceeds limit."}
        elif not condition_3:
            return {'is_eligible': False, 'error': "requested loan exceeds loan limit."}        
        else:
            return {'is_eligible': True, 'error': None}

class LoanRepaymentView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]
        
    def post(self, request):
        user=request.user
        amount_paid =request.data.get("amount_paid")
        
        if amount_paid>0:
            all_loans=user.loans.filter(is_active=True)
            if all_loans.exists():
                user.loan_owed-=amount_paid
                user.save()
                
                amount_to_redistribute=amount_paid
                for loan in all_loans:
                    if amount_to_redistribute<=0:
                        break
                    
                    repayment_amount=min(amount_to_redistribute, loan.remaining_amount)
                    
                    loan.repaid_amount+=repayment_amount
                    loan.save()
                    if repayment_amount !=0:
                        after_repay_loan.send(sender=None, user=user, loan=loan, amount=repayment_amount)
                    
                    amount_to_redistribute-=repayment_amount
                
                response_dict=dict(message="repayment of loan successful")
                return Response(response_dict, status=status.HTTP_200_OK)
            else:
                response_dict=dict(message="No active loans found")
                return Response(response_dict, status=status.HTTP_200_OK)
        else:
            response_dict=dict(message="amount not provided")
            return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)  
        
class LoanTransactionView(APIView):
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        transactions = LoanTransaction.objects.filter(user=user)
        serializer = LoanTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

class UserLoanInfoView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):        
        return self.request.user
