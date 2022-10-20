import json
import sys
import urllib.parse

class ChangeSet:
  data = None

  def __init__(self, data):
    self.data = data
    
  def status(self):
    status = self.data["Status"]
    color = "e3b341"
    
    if status == "CREATE_COMPLETE":
      color = "238636"
    elif status == "FAILED":
      color = "f85149"
    
    return "<img alt='%s' src='https://shields.io/badge/-%s-%s' />" % (status, status, color)
    
  def stack_name(self):
    return self.data["StackName"]
    
  def stack_id(self):
    return self.data["StackId"]
    
  def change_set_id(self):
    return self.data["ChangeSetId"]
    
  def changes(self):
    return self.data["Changes"]
  
class Change:
  data = None

  def __init__(self, data):
    self.data = data

  def action(self):
    action = self.data["ResourceChange"]["Action"].title()
    color = "e3b341"
    
    if action == "Modify":
      color = "1f6feb"
    elif action == "Add":
      color = "238636"
    elif action == "Remove":
      color = "f85149"
   
    return "<img alt='%s' src='https://shields.io/badge/-%s-%s' />" % (action, action, color)

  def logical_resource_id(self):
    return self.data["ResourceChange"]["LogicalResourceId"]
    
  def resource_type(self):
    return self.data["ResourceChange"]["ResourceType"]

  def replacement(self):
    if "Replacement" in self.data["ResourceChange"]:
      return self.data["ResourceChange"]["Replacement"]
      
    return "-"
    
  def is_conditional_replacement(self):
    return self.replacement() == "Conditional"
    
  def details(self):
    return self.data["ResourceChange"]["Details"]

class Detail:
  data = None
  
  def __init__(self, data):
    self.data = data
    
  def target(self):
    if "Name" in self.data["Target"]:
      return self.data["Target"]["Name"]
      
    return self.data["Target"]["Attribute"]
    
  def requires_recreation(self):
    if "RequiresRecreation" in self.data["Target"]:
      return self.data["Target"]["RequiresRecreation"]
    
    return "-"
    
  def always_requires_recreation(self):
    return self.requires_recreation() == "Always"
    
  def conditionally_requires_recreation(self):
    return self.requires_recreation() == "Conditionally"
    
  def is_dynamic_evaluation(self):
    if "Evaluation" in self.data:
      return self.data["Evaluation"] == "Dynamic"
      
    return False

class DetailAggregate:
  details = None

  def __init__(self):
    self.details = []

  def add_detail(self, detail):
      self.details.append(detail)

  def has_probable_cause_of_conditional_replacement(self):
    for detail in self.details:
       if change.is_conditional_replacement() and ((detail.always_requires_recreation() and detail.is_dynamic_evaluation()) or detail.conditionally_requires_recreation()):
         return True

    return False

if __name__ == "__main__":
  data = json.load(sys.stdin)
    
  change_set = ChangeSet(data)
  
  stack_id = urllib.parse.quote_plus(change_set.stack_id())
  change_set_id = urllib.parse.quote_plus(change_set.change_set_id())
  stack_name = change_set.stack_name()
  status = change_set.status()

  body = "<h1><a href='https://console.aws.amazon.com/cloudformation/home#/stacks/changesets/changes?stackId=%s&changeSetId=%s'>ChangeSet for %s</a> %s</h1>" % (stack_id, change_set_id, stack_name, status)
  
  if len(data["Changes"]) > 0:
    has_probable_cause_of_conditional_replacement = False
  
    body += "<table>"
    
    body +="<tr>"
    body += "<th>Action</th>"
    body += "<th>Logical ID</th>"
    body += "<th>Replacement</th>"
    body += "<th><a href='https://docs.aws.amazon.com/AWSCloudFormation/latest/APIReference/API_ResourceChangeDetail.html'>Details</a></th>"
    body += "</tr>"
    
    for change_data in change_set.changes():
      change = Change(change_data)
      
      body += "<tr>"
      body += "<td>%s</td>" % change.action()
      body += "<td>%s</td>" % change.logical_resource_id()
      body += "<td>%s</td>" % change.replacement()
      body += "<td>"
      
      details = change.details()
      
      if (len(details) > 0):
        body += "<ul>"
      
        detail_aggregates = {}
      
        for detail_data in details:
          detail = Detail(detail_data)
          detail_target = detail.target()
          
          if not detail_target in detail_aggregates.keys():           
            detail_aggregates[detail_target] = DetailAggregate()

          detail_aggregates[detail_target].add_detail(detail)
          
        for detail_target, detail_aggregate in detail_aggregates.items():
          asterisks = ""

          if detail_aggregate.has_probable_cause_of_conditional_replacement():
            asterisks += " <sup>R</sup>"
            has_probable_cause_of_conditional_replacement = True

          body += "<li>%s%s</li>" % (detail_target, asterisks)
          
        body += "</ul>"
      else:
        body += "-"
      
      body += "</td>"
      body += "</tr>"
      
    body += "</table>"
    
    if has_probable_cause_of_conditional_replacement:
      body += "<br /><br /><sup>R</sup> This target appears to be causing Conditional Replacement."
      
  else:
    body += "No Changes. See ChangeSet for more details."
  
  sys.stdout.write(body)

